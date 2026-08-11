from unittest.mock import Mock, patch

from app.integrations.calendar.delete_calendar_event import (
    CALENDAR_EVENTS_URL,
    delete_calendar_event,
)


@patch(
    "app.integrations.calendar.delete_calendar_event.request_calendar"
)
def test_delete_calendar_event_uses_exact_ids_without_body(
    request_mock: Mock,
) -> None:
    result = delete_calendar_event(
        access_token="access-token",
        calendar_id="work/calendar",
        event_id="event/1",
    )

    assert result is None
    request_mock.assert_called_once_with(
        method="DELETE",
        url=(
            f"{CALENDAR_EVENTS_URL}/work%2Fcalendar"
            "/events/event%2F1"
        ),
        headers={"Authorization": "Bearer access-token"},
        params={"sendUpdates": "none"},
    )
