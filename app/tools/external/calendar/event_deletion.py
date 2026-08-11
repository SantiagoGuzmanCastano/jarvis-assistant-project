from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.calendar.delete_calendar_event import (
    delete_calendar_event,
)
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
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import (
    get_valid_google_access_token,
)


CALENDAR_EVENT_DELETE_SELECTION_STATE = (
    "calendar_event_delete_selection"
)
CALENDAR_PENDING_EVENT_DELETE_STATE = "calendar_pending_event_delete"


def _prepare_event_deletion(
    *,
    access_token: str,
    selected_event: dict,
    calendar_id: str,
    timezone: str,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict:
    if selected_event.get("is_recurring"):
        return {
            "success": False,
            "reason": "recurring_event_delete_not_supported",
            "message": "Recurring event deletion is not supported yet.",
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
    if provider_event.get("status") == "cancelled":
        return {
            "success": False,
            "reason": "event_already_deleted",
            "message": "The selected calendar event is already deleted.",
        }
    if provider_event.get("recurringEventId") or provider_event.get(
        "recurrence"
    ):
        return {
            "success": False,
            "reason": "recurring_event_delete_not_supported",
            "message": "Recurring event deletion is not supported yet.",
        }

    exact_event = format_calendar_event_candidate(
        event=provider_event,
        position=int(selected_event.get("position", 1)),
        default_timezone=timezone,
    )
    pending_event = public_calendar_event_candidate(exact_event)
    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_DELETE_STATE,
        payload={
            "calendar_id": calendar_id,
            "event": pending_event,
        },
        session=session,
    )

    return {
        "success": False,
        "requires_confirmation": True,
        "reason": "confirmation_required",
        "message": (
            "The event is ready for deletion and requires "
            "explicit confirmation."
        ),
        "pending_event": pending_event,
    }


def _confirm_event_deletion(
    *,
    user_id: int,
    conversation_id: int,
    session: Session,
) -> dict:
    pending_payload = get_tool_payload(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type=CALENDAR_PENDING_EVENT_DELETE_STATE,
        session=session,
    )
    if not isinstance(pending_payload, dict):
        return {
            "success": False,
            "reason": "missing_pending_event_delete",
            "message": "No pending calendar event deletion was found.",
        }

    calendar_id = pending_payload.get("calendar_id")
    pending_event = pending_payload.get("event")
    if (
        not isinstance(calendar_id, str)
        or not isinstance(pending_event, dict)
        or not isinstance(pending_event.get("event_id"), str)
    ):
        raise AppError(
            code="invalid_tool_state",
            message="The pending calendar event deletion is invalid.",
            status_code=500,
        )

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    delete_calendar_event(
        access_token=access_token,
        calendar_id=calendar_id,
        event_id=pending_event["event_id"],
    )
    delete_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )

    return {
        "success": True,
        "deleted_event": pending_event,
    }


def calendar_delete_event_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    if arguments.get("confirmed") is True:
        return _confirm_event_deletion(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

    selected_result_position = arguments.get(
        "selected_result_position"
    )
    if selected_result_position is not None:
        selection_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type=CALENDAR_EVENT_DELETE_SELECTION_STATE,
            session=session,
        )
        if not isinstance(selection_payload, dict):
            return {
                "success": False,
                "reason": "missing_event_selection",
                "message": "No previous calendar event selection was found.",
            }

        candidates = selection_payload.get("events")
        calendar_id = selection_payload.get("calendar_id")
        timezone = selection_payload.get("timezone")
        if (
            not isinstance(candidates, list)
            or not isinstance(calendar_id, str)
            or not isinstance(timezone, str)
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

        access_token = get_valid_google_access_token(
            user_id=user_id,
            session=session,
        )
        return _prepare_event_deletion(
            access_token=access_token,
            selected_event=candidates[selected_result_position - 1],
            calendar_id=calendar_id,
            timezone=timezone,
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
    response = search_calendar_events(
        access_token=access_token,
        calendar_id=calendar_id,
        timezone=timezone,
        query=build_calendar_search_query(
            title=arguments.get("title"),
            description=arguments.get("description"),
        ),
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
            state_type=CALENDAR_EVENT_DELETE_SELECTION_STATE,
            payload={
                "events": candidates,
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
                "Select one before deleting it."
            ),
            "matching_events": matching_events,
            "returned_count": len(matching_events),
            "has_more": has_more,
        }

    return _prepare_event_deletion(
        access_token=access_token,
        selected_event=candidates[0],
        calendar_id=calendar_id,
        timezone=timezone,
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
