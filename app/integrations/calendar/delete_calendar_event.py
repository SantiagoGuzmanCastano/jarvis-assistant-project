from urllib.parse import quote

from app.integrations.calendar.client import request_calendar


CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars"


def delete_calendar_event(
    access_token: str,
    calendar_id: str,
    event_id: str,
) -> None:
    encoded_calendar_id = quote(calendar_id, safe="")
    encoded_event_id = quote(event_id, safe="")
    request_calendar(
        method="DELETE",
        url=(
            f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}"
            f"/events/{encoded_event_id}"
        ),
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        params={"sendUpdates": "none"},
    )
