from unittest.mock import Mock, patch

from app.integrations.calendar.create_calendar_event import (
    CALENDAR_EVENTS_URL,
    create_calendar_event,
)
from app.integrations.calendar.events import list_calendar_events


@patch(
    "app.integrations.calendar.create_calendar_event.request_calendar"
)
def test_create_calendar_event_builds_exact_google_request(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {"id": "event-1"}
    request_mock.return_value = response

    result = create_calendar_event(
        title="Reunión Jarvis",
        description="Revisar el MVP",
        start_date="2026-08-01T10:00:00-05:00",  # type: ignore[arg-type]
        end_date="2026-08-01T11:00:00-05:00",  # type: ignore[arg-type]
        access_token="access-token",
        calendar_id="work/calendar",
        timezone="America/Bogota",
        location="Sala principal",
    )

    assert result == {"id": "event-1"}
    request_mock.assert_called_once_with(
        method="POST",
        url=f"{CALENDAR_EVENTS_URL}/work%2Fcalendar/events",
        headers={"Authorization": "Bearer access-token"},
        params={"sendUpdates": "none"},
        json={
            "summary": "Reunión Jarvis",
            "description": "Revisar el MVP",
            "location": "Sala principal",
            "start": {
                "dateTime": "2026-08-01T10:00:00-05:00",
                "timeZone": "America/Bogota",
            },
            "end": {
                "dateTime": "2026-08-01T11:00:00-05:00",
                "timeZone": "America/Bogota",
            },
        },
    )


@patch(
    "app.integrations.calendar.create_calendar_event.request_calendar"
)
def test_create_calendar_event_omits_unsupplied_optional_fields(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {"id": "event-1"}
    request_mock.return_value = response

    create_calendar_event(
        title="Reunión Jarvis",
        description=None,
        start_date="2026-08-01T10:00:00-05:00",  # type: ignore[arg-type]
        end_date="2026-08-01T11:00:00-05:00",  # type: ignore[arg-type]
        access_token="access-token",
        calendar_id="primary",
        timezone="America/Bogota",
        location=None,
    )

    request_body = request_mock.call_args.kwargs["json"]
    assert "description" not in request_body
    assert "location" not in request_body


@patch("app.integrations.calendar.events.request_calendar")
def test_list_calendar_events_builds_ordered_bounded_request(
    request_mock: Mock,
) -> None:
    response = Mock()
    response.json.return_value = {
        "items": [{"id": "event-1"}],
        "nextPageToken": "next-page",
    }
    request_mock.return_value = response

    result = list_calendar_events(
        access_token="access-token",
        calendar_id="work/calendar",
        timezone="America/Bogota",
        time_min="2026-08-01T00:00:00-05:00",
        time_max="2026-08-08T00:00:00-05:00",
        max_results=10,
    )

    assert result == {
        "items": [{"id": "event-1"}],
        "nextPageToken": "next-page",
    }
    request_mock.assert_called_once_with(
        method="GET",
        url=f"{CALENDAR_EVENTS_URL}/work%2Fcalendar/events",
        headers={"Authorization": "Bearer access-token"},
        params={
            "timeMin": "2026-08-01T00:00:00-05:00",
            "timeMax": "2026-08-08T00:00:00-05:00",
            "timeZone": "America/Bogota",
            "singleEvents": "true",
            "orderBy": "startTime",
            "showDeleted": "false",
            "maxResults": 10,
        },
    )
