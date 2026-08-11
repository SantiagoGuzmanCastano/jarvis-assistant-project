from urllib.parse import quote

from app.integrations.calendar.client import request_calendar


CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars"


def list_calendar_events(
    access_token: str,
    calendar_id: str,
    timezone: str,
    time_min: str,
    time_max: str,
    max_results: int,
) -> dict:
    encoded_calendar_id = quote(calendar_id, safe="")
    response = request_calendar(
        method="GET",
        url=f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}/events",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        params={
            "timeMin": time_min,
            "timeMax": time_max,
            "timeZone": timezone,
            "singleEvents": "true",
            "orderBy": "startTime",
            "showDeleted": "false",
            "maxResults": max_results,
        },
    )

    return response.json()


def search_calendar_events(
    access_token: str,
    calendar_id: str,
    timezone: str,
    query: str,
    time_min: str | None,
    time_max: str | None,
    max_results: int,
) -> dict:
    encoded_calendar_id = quote(calendar_id, safe="")
    params: dict[str, str | int] = {
        "timeZone": timezone,
        "singleEvents": "true",
        "orderBy": "startTime",
        "showDeleted": "false",
        "maxResults": max_results,
    }

    if query:
        params["q"] = query
    if time_min is not None:
        params["timeMin"] = time_min
    if time_max is not None:
        params["timeMax"] = time_max

    response = request_calendar(
        method="GET",
        url=f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}/events",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        params=params,
    )

    return response.json()


def get_calendar_event(
    access_token: str,
    calendar_id: str,
    event_id: str,
    timezone: str,
) -> dict:
    encoded_calendar_id = quote(calendar_id, safe="")
    encoded_event_id = quote(event_id, safe="")
    response = request_calendar(
        method="GET",
        url=(
            f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}"
            f"/events/{encoded_event_id}"
        ),
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        params={"timeZone": timezone},
    )

    return response.json()
