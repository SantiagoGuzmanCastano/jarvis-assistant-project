from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.calendar.event_candidates import (
    format_calendar_event_candidate,
    invalid_calendar_event_response,
    public_calendar_event_candidate,
)
from app.integrations.calendar.events import (
    get_calendar_event,
    search_calendar_events,
)
from app.integrations.calendar.search import build_calendar_search_query
from app.integrations.calendar.update_calendar_event import (
    patch_calendar_event,
)
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import (
    get_valid_google_access_token,
)


CALENDAR_EVENT_UPDATE_SELECTION_STATE = (
    "calendar_event_update_selection"
)
CALENDAR_PENDING_EVENT_UPDATE_STATE = "calendar_pending_event_update"

UPDATE_ARGUMENT_FIELDS = {
    "new_title": "title",
    "new_description": "description",
    "new_start_date": "start_date",
    "new_end_date": "end_date",
    "new_location": "location",
}


def _parse_event_datetime(value: str, timezone: str) -> datetime:
    try:
        parsed_value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as error:
        raise invalid_calendar_event_response(
            "Google Calendar returned an invalid event date."
        ) from error

    if parsed_value.utcoffset() is None:
        try:
            parsed_value = parsed_value.replace(
                tzinfo=ZoneInfo(timezone)
            )
        except ZoneInfoNotFoundError as error:
            raise invalid_calendar_event_response(
                "Google Calendar returned an invalid event timezone."
            ) from error

    return parsed_value


def _format_timed_event(event: dict, default_timezone: str) -> dict:
    event_id = event.get("id")
    start = event.get("start")
    end = event.get("end")
    if (
        not isinstance(event_id, str)
        or not event_id
        or not isinstance(start, dict)
        or not isinstance(end, dict)
    ):
        raise invalid_calendar_event_response(
            "Google Calendar returned an invalid event."
        )

    start_value = start.get("dateTime")
    end_value = end.get("dateTime")
    if not isinstance(start_value, str) or not isinstance(end_value, str):
        raise AppError(
            code="calendar_all_day_update_not_supported",
            message="All-day event updates are not supported yet.",
            status_code=422,
        )

    timezone = start.get("timeZone") or default_timezone
    start_date = _parse_event_datetime(start_value, timezone)
    end_date = _parse_event_datetime(end_value, timezone)
    if end_date <= start_date:
        raise invalid_calendar_event_response(
            "Google Calendar returned an invalid event range."
        )

    return {
        "event_id": event_id,
        "title": (
            event.get("summary")
            if isinstance(event.get("summary"), str)
            else None
        ),
        "description": (
            event.get("description")
            if isinstance(event.get("description"), str)
            else None
        ),
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "timezone": timezone,
        "location": (
            event.get("location")
            if isinstance(event.get("location"), str)
            else None
        ),
        "html_link": (
            event.get("htmlLink")
            if isinstance(event.get("htmlLink"), str)
            else None
        ),
    }


def _extract_requested_changes(arguments: dict) -> dict:
    return {
        update_field: arguments[argument_field]
        for argument_field, update_field in UPDATE_ARGUMENT_FIELDS.items()
        if arguments.get(argument_field) is not None
    }


def _prepare_update(
    *,
    access_token: str,
    selected_event: dict,
    changes: dict,
    calendar_id: str,
    timezone: str,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict:
    if selected_event.get("is_recurring"):
        return {
            "success": False,
            "reason": "recurring_event_update_not_supported",
            "message": "Recurring event updates are not supported yet.",
        }
    if selected_event.get("all_day"):
        return {
            "success": False,
            "reason": "all_day_event_update_not_supported",
            "message": "All-day event updates are not supported yet.",
        }

    event_id = selected_event.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise AppError(
            code="invalid_tool_state",
            message="The selected calendar event is invalid.",
            status_code=500,
        )

    provider_event = get_calendar_event(
        access_token=access_token,
        calendar_id=calendar_id,
        event_id=event_id,
        timezone=timezone,
    )
    if provider_event.get("recurringEventId") or provider_event.get(
        "recurrence"
    ):
        return {
            "success": False,
            "reason": "recurring_event_update_not_supported",
            "message": "Recurring event updates are not supported yet.",
        }
    provider_start = provider_event.get("start")
    provider_end = provider_event.get("end")
    if (
        not isinstance(provider_start, dict)
        or not isinstance(provider_end, dict)
        or "dateTime" not in provider_start
        or "dateTime" not in provider_end
    ):
        return {
            "success": False,
            "reason": "all_day_event_update_not_supported",
            "message": "All-day event updates are not supported yet.",
        }

    current_event = _format_timed_event(
        event=provider_event,
        default_timezone=timezone,
    )
    current_snapshot = {
        key: current_event[key]
        for key in (
            "title",
            "description",
            "start_date",
            "end_date",
            "timezone",
            "location",
        )
    }
    proposed_event = {**current_snapshot, **changes}
    if "start_date" in changes or "end_date" in changes:
        proposed_event["timezone"] = timezone

    proposed_start = _parse_event_datetime(
        proposed_event["start_date"],
        proposed_event["timezone"],
    )
    proposed_end = _parse_event_datetime(
        proposed_event["end_date"],
        proposed_event["timezone"],
    )
    if proposed_end <= proposed_start:
        return {
            "success": False,
            "reason": "invalid_proposed_event_range",
            "message": (
                "The proposed event end must be later than its start."
            ),
        }

    updated_fields = list(changes)
    pending_payload = {
        "event_id": current_event["event_id"],
        "calendar_id": calendar_id,
        "timezone": proposed_event["timezone"],
        "changes": changes,
        "updated_fields": updated_fields,
        "current_event": current_snapshot,
        "proposed_event": proposed_event,
    }
    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_UPDATE_STATE,
        payload=pending_payload,
        session=session,
    )

    return {
        "success": False,
        "requires_confirmation": True,
        "reason": "confirmation_required",
        "message": (
            "The event update is ready and requires explicit confirmation."
        ),
        "pending_update": {
            "current_event": current_snapshot,
            "proposed_event": proposed_event,
            "updated_fields": updated_fields,
        },
    }


def _values_match(field_name: str, actual: object, expected: object) -> bool:
    if field_name in {"start_date", "end_date"}:
        if not isinstance(actual, str) or not isinstance(expected, str):
            return False
        return _parse_event_datetime(
            actual,
            "UTC",
        ) == _parse_event_datetime(expected, "UTC")

    if field_name in {"description", "location"}:
        return (actual or "") == (expected or "")

    return actual == expected


def _confirm_update(
    *,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict:
    pending_update = get_tool_payload(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_UPDATE_STATE,
        session=session,
    )
    if not isinstance(pending_update, dict):
        return {
            "success": False,
            "reason": "missing_pending_event_update",
            "message": "No pending calendar event update was found.",
        }

    event_id = pending_update.get("event_id")
    calendar_id = pending_update.get("calendar_id")
    timezone = pending_update.get("timezone")
    changes = pending_update.get("changes")
    updated_fields = pending_update.get("updated_fields")
    if (
        not isinstance(event_id, str)
        or not isinstance(calendar_id, str)
        or not isinstance(timezone, str)
        or not isinstance(changes, dict)
        or not changes
        or not isinstance(updated_fields, list)
    ):
        raise AppError(
            code="invalid_tool_state",
            message="The pending calendar event update is invalid.",
            status_code=500,
        )

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    response = patch_calendar_event(
        access_token=access_token,
        calendar_id=calendar_id,
        event_id=event_id,
        timezone=timezone,
        changes=changes,
    )
    if response.get("id") != event_id:
        raise invalid_calendar_event_response(
            "Google Calendar did not confirm the event update."
        )

    updated_event = _format_timed_event(
        event=response,
        default_timezone=timezone,
    )
    for field_name, expected_value in changes.items():
        if not _values_match(
            field_name,
            updated_event.get(field_name),
            expected_value,
        ):
            raise invalid_calendar_event_response(
                "Google Calendar did not confirm the event update."
            )

    delete_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )

    return {
        "success": True,
        "event": {
            **updated_event,
            "calendar_id": calendar_id,
        },
        "updated_fields": updated_fields,
    }


def calendar_update_event_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    if arguments.get("confirmed") is True:
        return _confirm_update(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

    selected_result_position = arguments.get(
        "selected_result_position"
    )
    requested_changes = _extract_requested_changes(arguments)

    if selected_result_position is not None:
        selection_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=CALENDAR_EVENT_UPDATE_SELECTION_STATE,
            session=session,
        )
        if not isinstance(selection_payload, dict):
            return {
                "success": False,
                "reason": "missing_event_selection",
                "message": "No previous calendar event selection was found.",
            }

        candidates = selection_payload.get("events")
        stored_changes = selection_payload.get("changes")
        if not isinstance(candidates, list) or not isinstance(
            stored_changes,
            dict,
        ):
            raise AppError(
                code="invalid_tool_state",
                message="The calendar event selection is invalid.",
                status_code=500,
            )
        if selected_result_position > len(candidates):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected calendar event position is out of range.",
            }

        changes = {**stored_changes, **requested_changes}
        access_token = get_valid_google_access_token(
            user_id=user_id,
            session=session,
        )
        return _prepare_update(
            access_token=access_token,
            selected_event=candidates[selected_result_position - 1],
            changes=changes,
            calendar_id=selection_payload["calendar_id"],
            timezone=selection_payload["timezone"],
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

    timezone = arguments.get("timezone", "America/Bogota")
    calendar_id = arguments.get("calendar_id", "primary")
    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    query = build_calendar_search_query(
        title=arguments.get("title"),
        description=arguments.get("description"),
    )
    response = search_calendar_events(
        access_token=access_token,
        calendar_id=calendar_id,
        timezone=timezone,
        query=query,
        time_min=arguments.get("start_date"),
        time_max=arguments.get("end_date"),
        max_results=int(arguments.get("max_results", 10)),
    )

    provider_events = response.get("items", [])
    if not isinstance(provider_events, list) or any(
        not isinstance(event, dict) for event in provider_events
    ):
        raise invalid_calendar_event_response(
            "Google Calendar returned an invalid event list."
        )

    active_provider_events = [
        event
        for event in provider_events
        if event.get("status") != "cancelled"
    ]
    candidates = [
        format_calendar_event_candidate(
            event=event,
            position=position,
            default_timezone=timezone,
        )
        for position, event in enumerate(
            active_provider_events,
            start=1,
        )
    ]
    has_more = bool(response.get("nextPageToken"))

    if not candidates:
        return {
            "success": False,
            "reason": "no_matching_event",
            "message": "No matching calendar event was found.",
        }

    if len(candidates) > 1 or has_more:
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=CALENDAR_EVENT_UPDATE_SELECTION_STATE,
            payload={
                "events": candidates,
                "changes": requested_changes,
                "calendar_id": calendar_id,
                "timezone": timezone,
            },
            session=session,
        )
        matching_events = [
            public_calendar_event_candidate(candidate)
            for candidate in candidates
        ]
        return {
            "success": False,
            "requires_selection": True,
            "reason": "multiple_matching_events",
            "message": (
                "Multiple matching calendar events were found. "
                "Select one before updating it."
            ),
            "matching_events": matching_events,
            "returned_count": len(matching_events),
            "has_more": has_more,
        }

    return _prepare_update(
        access_token=access_token,
        selected_event=candidates[0],
        changes=requested_changes,
        calendar_id=calendar_id,
        timezone=timezone,
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
