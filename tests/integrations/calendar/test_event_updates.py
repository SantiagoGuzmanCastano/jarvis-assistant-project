from unittest.mock import Mock, patch

from app.integrations.calendar.events import (
    CALENDAR_EVENTS_URL,
    get_calendar_event,
    search_calendar_events,
)
from app.integrations.calendar.update_calendar_event import (
    patch_calendar_event,
)


@patch("app.integrations.calendar.events.request_calendar")
def test_search_calendar_events_builds_filtered_request(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {"items": []}
    request_mock.return_value = response

    result = search_calendar_events(
        access_token="access-token",
        calendar_id="work/calendar",
        timezone="America/Bogota",
        query="Jarvis Phase 9",
        time_min="2026-08-01T00:00:00-05:00",
        time_max=None,
        max_results=10,
    )

    assert result == {"items": []}
    request_mock.assert_called_once_with(
        method="GET",
        url=f"{CALENDAR_EVENTS_URL}/work%2Fcalendar/events",
        headers={"Authorization": "Bearer access-token"},
        params={
            "timeZone": "America/Bogota",
            "singleEvents": "true",
            "orderBy": "startTime",
            "showDeleted": "false",
            "maxResults": 10,
            "q": "Jarvis Phase 9",
            "timeMin": "2026-08-01T00:00:00-05:00",
        },
    )


@patch("app.integrations.calendar.events.request_calendar")
def test_get_calendar_event_uses_exact_encoded_event_id(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {"id": "event/1"}
    request_mock.return_value = response

    result = get_calendar_event(
        access_token="access-token",
        calendar_id="primary",
        event_id="event/1",
        timezone="America/Bogota",
    )

    assert result == {"id": "event/1"}
    request_mock.assert_called_once_with(
        method="GET",
        url=f"{CALENDAR_EVENTS_URL}/primary/events/event%2F1",
        headers={"Authorization": "Bearer access-token"},
        params={"timeZone": "America/Bogota"},
    )


@patch(
    "app.integrations.calendar.update_calendar_event.request_calendar"
)
def test_patch_calendar_event_sends_only_requested_fields(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {"id": "event-1"}
    request_mock.return_value = response

    result = patch_calendar_event(
        access_token="access-token",
        calendar_id="primary",
        event_id="event-1",
        timezone="America/Bogota",
        changes={
            "title": "Revisión Phase 9",
            "start_date": "2026-08-01T14:00:00-05:00",
        },
    )

    assert result == {"id": "event-1"}
    request_mock.assert_called_once_with(
        method="PATCH",
        url=(
            "https://www.googleapis.com/calendar/v3/calendars/"
            "primary/events/event-1"
        ),
        headers={"Authorization": "Bearer access-token"},
        params={"sendUpdates": "none"},
        json={
            "summary": "Revisión Phase 9",
            "start": {
                "dateTime": "2026-08-01T14:00:00-05:00",
                "timeZone": "America/Bogota",
            },
        },
    )
