from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.calendar.events import list_calendar_events
from app.services.external_auth_service import get_valid_google_access_token


DEFAULT_UPCOMING_RANGE_DAYS = 7


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def _format_upcoming_event(event: dict, default_timezone: str) -> dict:
    event_id = event.get("id")
    start = event.get("start")
    end = event.get("end")

    if (
        not isinstance(event_id, str)
        or not event_id
        or not isinstance(start, dict)
        or not isinstance(end, dict)
    ):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned an invalid event.",
            status_code=502,
        )

    start_value = start.get("dateTime") or start.get("date")
    end_value = end.get("dateTime") or end.get("date")
    if not isinstance(start_value, str) or not isinstance(end_value, str):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned an event without a valid range.",
            status_code=502,
        )

    provider_attendees = event.get("attendees", [])
    if not isinstance(provider_attendees, list):
        provider_attendees = []

    attendees = [
        attendee["email"]
        for attendee in provider_attendees
        if isinstance(attendee, dict)
        and isinstance(attendee.get("email"), str)
    ]

    return {
        "event_id": event_id,
        "title": event.get("summary"),
        "description": event.get("description"),
        "start_date": start_value,
        "end_date": end_value,
        "timezone": start.get("timeZone") or default_timezone,
        "all_day": "date" in start and "dateTime" not in start,
        "location": event.get("location"),
        "html_link": event.get("htmlLink"),
        "attendees": attendees,
    }


def calendar_get_upcoming_events_tool(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    timezone = arguments.get("timezone", "America/Bogota")
    calendar_id = arguments.get("calendar_id", "primary")
    max_results = int(arguments.get("max_results", 10))
    now = datetime.now(ZoneInfo(timezone))

    range_start = _parse_datetime(arguments.get("start_date")) or now
    range_end = _parse_datetime(arguments.get("end_date"))
    if range_end is None:
        range_end = range_start + timedelta(
            days=DEFAULT_UPCOMING_RANGE_DAYS
        )

    if range_end <= range_start:
        raise AppError(
            code="invalid_tool_arguments",
            message="The calendar date range is invalid.",
            status_code=422,
        )

    access_token = get_valid_google_access_token(
        user_id=user_id,
        session=session,
    )
    response = list_calendar_events(
        access_token=access_token,
        calendar_id=calendar_id,
        timezone=timezone,
        time_min=range_start.isoformat(),
        time_max=range_end.isoformat(),
        max_results=max_results,
    )

    provider_events = response.get("items", [])
    if not isinstance(provider_events, list):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned an invalid event list.",
            status_code=502,
        )
    if any(not isinstance(event, dict) for event in provider_events):
        raise AppError(
            code="external_provider_invalid_response",
            message="Google Calendar returned an invalid event list.",
            status_code=502,
        )

    events = [
        _format_upcoming_event(
            event=event,
            default_timezone=timezone,
        )
        for event in provider_events
    ]

    return {
        "success": True,
        "events": events,
        "returned_count": len(events),
        "has_more": bool(response.get("nextPageToken")),
        "range_start": range_start,
        "range_end": range_end,
        "timezone": timezone,
        "calendar_id": calendar_id,
    }
