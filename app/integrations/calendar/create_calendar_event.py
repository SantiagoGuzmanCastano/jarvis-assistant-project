

from datetime import datetime
from urllib.parse import quote

from app.integrations.calendar.client import request_calendar


CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars"


def create_calendar_event(
    title: str,
    description: str | None,
    start_date: datetime,
    end_date: datetime,
    access_token: str,
    calendar_id: str,
    timezone: str,
    location: str | None = None,
) -> dict:

    event = {
        "summary": title,
        "start": {
            "dateTime": start_date,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_date,
            "timeZone": timezone,
        },
    }

    if description is not None:
        event["description"] = description
    if location is not None:
        event["location"] = location

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    encoded_calendar_id = quote(calendar_id, safe="")
    response = request_calendar(
        method="POST",
        url=f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}/events",
        headers=headers,
        params={"sendUpdates": "none"},
        json=event,
    )

    return response.json()
