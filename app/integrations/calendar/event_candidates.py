from app.core.errors import AppError


def invalid_calendar_event_response(message: str) -> AppError:
    return AppError(
        code="external_provider_invalid_response",
        message=message,
        status_code=502,
    )


def format_calendar_event_candidate(
    event: dict,
    position: int,
    default_timezone: str,
) -> dict:
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
            "Google Calendar returned an invalid event candidate."
        )

    start_value = start.get("dateTime") or start.get("date")
    end_value = end.get("dateTime") or end.get("date")
    if not isinstance(start_value, str) or not isinstance(end_value, str):
        raise invalid_calendar_event_response(
            "Google Calendar returned an event without a valid range."
        )

    return {
        "position": position,
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
        "start_date": start_value,
        "end_date": end_value,
        "timezone": start.get("timeZone") or default_timezone,
        "all_day": "date" in start and "dateTime" not in start,
        "location": (
            event.get("location")
            if isinstance(event.get("location"), str)
            else None
        ),
        "is_recurring": bool(
            event.get("recurringEventId") or event.get("recurrence")
        ),
    }


def public_calendar_event_candidate(candidate: dict) -> dict:
    return {
        key: value
        for key, value in candidate.items()
        if key != "is_recurring"
    }
