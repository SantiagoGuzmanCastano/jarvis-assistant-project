from urllib.parse import quote

from app.integrations.calendar.client import request_calendar


CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars"


def patch_calendar_event(
    access_token: str,
    calendar_id: str,
    event_id: str,
    timezone: str,
    changes: dict,
) -> dict:
    event_patch = {}

    if "title" in changes:
        event_patch["summary"] = changes["title"]
    if "description" in changes:
        event_patch["description"] = changes["description"]
    if "location" in changes:
        event_patch["location"] = changes["location"]
    if "start_date" in changes:
        event_patch["start"] = {
            "dateTime": changes["start_date"],
            "timeZone": timezone,
        }
    if "end_date" in changes:
        event_patch["end"] = {
            "dateTime": changes["end_date"],
            "timeZone": timezone,
        }

    encoded_calendar_id = quote(calendar_id, safe="")
    encoded_event_id = quote(event_id, safe="")
    response = request_calendar(
        method="PATCH",
        url=(
            f"{CALENDAR_EVENTS_URL}/{encoded_calendar_id}"
            f"/events/{encoded_event_id}"
        ),
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        params={"sendUpdates": "none"},
        json=event_patch,
    )

    return response.json()
