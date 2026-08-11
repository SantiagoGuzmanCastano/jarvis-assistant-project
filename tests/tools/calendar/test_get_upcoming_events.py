from datetime import datetime
from unittest.mock import Mock

import pytest

from app.core.errors import AppError
from app.schemas.tools.calendar import CalendarGetUpcomingEventsArguments
from app.schemas.tools.calendar_results import CalendarGetUpcomingEventsResult
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.tool_execution import build_tool_context, tool_execution_system
from app.tools.external.calendar import event_listings
from app.tools.registry import TOOLS


def test_get_upcoming_events_is_registered_as_read_only_calendar_tool() -> None:
    definition = TOOLS["calendar_get_upcoming_events"]

    assert definition["arguments_schema"] is CalendarGetUpcomingEventsArguments
    assert definition["result_schema"] is CalendarGetUpcomingEventsResult
    assert definition.get("requires_conversation_id", False) is False
    assert "calendar_get_upcoming_events" in CALENDAR_TOOL_NAMES


def test_get_upcoming_events_formats_timed_and_all_day_events(
    monkeypatch,
) -> None:
    session = Mock()
    list_events_mock = Mock(
        return_value={
            "items": [
                {
                    "id": "timed-1",
                    "summary": "Reunión Jarvis",
                    "description": "Revisar backend",
                    "location": "Meet",
                    "start": {
                        "dateTime": "2026-08-01T10:00:00-05:00",
                        "timeZone": "America/Bogota",
                    },
                    "end": {
                        "dateTime": "2026-08-01T11:00:00-05:00",
                        "timeZone": "America/Bogota",
                    },
                    "attendees": [
                        {"email": "lina@example.com"},
                        {"displayName": "Sin correo"},
                    ],
                    "htmlLink": "https://calendar.google.com/event?eid=timed-1",
                },
                {
                    "id": "all-day-1",
                    "summary": "Planeación",
                    "start": {"date": "2026-08-02"},
                    "end": {"date": "2026-08-03"},
                },
            ],
            "nextPageToken": "next-page",
        }
    )
    monkeypatch.setattr(
        event_listings,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_listings,
        "list_calendar_events",
        list_events_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_get_upcoming_events",
        arguments={
            "start_date": "2026-08-01T00:00:00-05:00",
            "end_date": "2026-08-04T00:00:00-05:00",
            "max_results": 2,
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["returned_count"] == 2
    assert result["has_more"] is True
    assert result["events"][0] == {
        "event_id": "timed-1",
        "title": "Reunión Jarvis",
        "description": "Revisar backend",
        "start_date": "2026-08-01T10:00:00-05:00",
        "end_date": "2026-08-01T11:00:00-05:00",
        "timezone": "America/Bogota",
        "all_day": False,
        "location": "Meet",
        "html_link": "https://calendar.google.com/event?eid=timed-1",
        "attendees": ["lina@example.com"],
    }
    assert result["events"][1]["start_date"] == "2026-08-02"
    assert result["events"][1]["end_date"] == "2026-08-03"
    assert result["events"][1]["all_day"] is True
    assert result["events"][1]["timezone"] == "America/Bogota"
    list_events_mock.assert_called_once_with(
        access_token="access-token",
        calendar_id="primary",
        timezone="America/Bogota",
        time_min="2026-08-01T00:00:00-05:00",
        time_max="2026-08-04T00:00:00-05:00",
        max_results=2,
    )


def test_get_upcoming_events_defaults_to_a_seven_day_range(
    monkeypatch,
) -> None:
    list_events_mock = Mock(return_value={"items": []})
    monkeypatch.setattr(
        event_listings,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_listings,
        "list_calendar_events",
        list_events_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_get_upcoming_events",
        arguments={},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    range_start = datetime.fromisoformat(result["range_start"])
    range_end = datetime.fromisoformat(result["range_end"])
    assert (range_end - range_start).days == 7
    assert result["events"] == []
    assert result["returned_count"] == 0
    assert result["has_more"] is False
    assert range_start.utcoffset() is not None
    assert list_events_mock.call_args.kwargs["time_min"] == range_start.isoformat()
    assert list_events_mock.call_args.kwargs["time_max"] == range_end.isoformat()


def test_get_upcoming_events_rejects_invalid_provider_items(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        event_listings,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_listings,
        "list_calendar_events",
        Mock(return_value={"items": ["invalid-event"]}),
    )

    with pytest.raises(AppError) as error_info:
        tool_execution_system(
            tool_name="calendar_get_upcoming_events",
            arguments={},
            user_id=7,
            session=Mock(),
            conversation_id=11,
        )

    assert error_info.value.code == "external_provider_invalid_response"
    assert error_info.value.status_code == 502


def test_get_upcoming_events_context_explains_read_only_results() -> None:
    context = build_tool_context(
        "calendar_get_upcoming_events",
        {
            "success": True,
            "events": [],
            "returned_count": 0,
            "has_more": False,
            "range_start": "2026-08-01T00:00:00-05:00",
            "range_end": "2026-08-08T00:00:00-05:00",
            "timezone": "America/Bogota",
            "calendar_id": "primary",
        },
    )

    assert "no events were found" in context
    assert "Do not claim that Calendar was modified" in context
