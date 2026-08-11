from unittest.mock import Mock

import pytest

from app.schemas.tools.calendar import CalendarDeleteEventArguments
from app.schemas.tools.calendar_results import CalendarDeleteEventResult
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.intent_router import build_tool_intent_prompt
from app.services.intent_router_parser import parse_tool_intent_response
from app.services.tool_execution import (
    build_tool_context,
    tool_execution_system,
)
from app.tools.external.calendar import event_deletion
from app.tools.registry import TOOLS


def _timed_event(
    *,
    event_id: str = "event-1",
    title: str = "Reunión Jarvis",
) -> dict:
    return {
        "id": event_id,
        "status": "confirmed",
        "summary": title,
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
    }


def _all_day_event() -> dict:
    return {
        "id": "all-day-1",
        "status": "confirmed",
        "summary": "Día de planeación",
        "start": {"date": "2026-08-01"},
        "end": {"date": "2026-08-02"},
    }


def _patch_common_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_deletion,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )


def test_delete_event_is_registered_as_stateful_calendar_tool() -> None:
    definition = TOOLS["calendar_delete_event"]

    assert definition["arguments_schema"] is CalendarDeleteEventArguments
    assert definition["result_schema"] is CalendarDeleteEventResult
    assert definition["requires_conversation_id"] is True
    assert "calendar_delete_event" in CALENDAR_TOOL_NAMES


def test_delete_event_prepares_single_match_without_deleting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    create_state_mock = Mock()
    delete_event_mock = Mock()
    _patch_common_dependencies(monkeypatch)
    monkeypatch.setattr(
        event_deletion,
        "search_calendar_events",
        Mock(return_value={"items": [_timed_event()]}),
    )
    monkeypatch.setattr(
        event_deletion,
        "get_calendar_event",
        Mock(return_value=_timed_event()),
    )
    monkeypatch.setattr(
        event_deletion,
        "create_tool_state",
        create_state_mock,
    )
    monkeypatch.setattr(
        event_deletion,
        "delete_calendar_event",
        delete_event_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["requires_confirmation"] is True
    assert result["pending_event"]["event_id"] == "event-1"
    assert result["pending_event"]["title"] == "Reunión Jarvis"
    state_call = create_state_mock.call_args.kwargs
    assert (
        state_call["state_type"]
        == event_deletion.CALENDAR_PENDING_EVENT_DELETE_STATE
    )
    assert state_call["payload"]["event"]["event_id"] == "event-1"
    delete_event_mock.assert_not_called()


def test_delete_event_preserves_multiple_candidates_for_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_state_mock = Mock()
    get_event_mock = Mock()
    _patch_common_dependencies(monkeypatch)
    monkeypatch.setattr(
        event_deletion,
        "search_calendar_events",
        Mock(
            return_value={
                "items": [
                    _timed_event(event_id="event-1"),
                    _timed_event(
                        event_id="event-2",
                        title="Reunión Jarvis semanal",
                    ),
                ]
            }
        ),
    )
    monkeypatch.setattr(
        event_deletion,
        "get_calendar_event",
        get_event_mock,
    )
    monkeypatch.setattr(
        event_deletion,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_selection"] is True
    assert result["returned_count"] == 2
    assert [
        event["position"] for event in result["matching_events"]
    ] == [1, 2]
    assert [
        event["event_id"]
        for event in create_state_mock.call_args.kwargs["payload"]["events"]
    ] == ["event-1", "event-2"]
    get_event_mock.assert_not_called()


def test_delete_event_uses_saved_selected_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_state_mock = Mock()
    _patch_common_dependencies(monkeypatch)
    monkeypatch.setattr(
        event_deletion,
        "get_tool_payload",
        Mock(
            return_value={
                "events": [
                    {
                        "event_id": "event-1",
                        "position": 1,
                        "is_recurring": False,
                    },
                    {
                        "event_id": "event-2",
                        "position": 2,
                        "is_recurring": False,
                    },
                ],
                "calendar_id": "primary",
                "timezone": "America/Bogota",
            }
        ),
    )
    get_event_mock = Mock(
        return_value=_timed_event(event_id="event-2")
    )
    monkeypatch.setattr(
        event_deletion,
        "get_calendar_event",
        get_event_mock,
    )
    monkeypatch.setattr(
        event_deletion,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={
            "confirmed": False,
            "selected_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["pending_event"]["event_id"] == "event-2"
    assert result["pending_event"]["position"] == 2
    get_event_mock.assert_called_once()


def test_delete_event_confirmation_deletes_only_pending_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    pending_event = {
        "position": 1,
        "event_id": "event-1",
        "title": "Reunión Jarvis",
        "description": "Revisar backend",
        "start_date": "2026-08-01T10:00:00-05:00",
        "end_date": "2026-08-01T11:00:00-05:00",
        "timezone": "America/Bogota",
        "all_day": False,
        "location": "Meet",
    }
    monkeypatch.setattr(
        event_deletion,
        "get_tool_payload",
        Mock(
            return_value={
                "calendar_id": "primary",
                "event": pending_event,
            }
        ),
    )
    _patch_common_dependencies(monkeypatch)
    delete_event_mock = Mock()
    delete_state_mock = Mock()
    monkeypatch.setattr(
        event_deletion,
        "delete_calendar_event",
        delete_event_mock,
    )
    monkeypatch.setattr(
        event_deletion,
        "delete_tool_state",
        delete_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={"confirmed": True},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["deleted_event"]["event_id"] == "event-1"
    delete_event_mock.assert_called_once_with(
        access_token="access-token",
        calendar_id="primary",
        event_id="event-1",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


def test_delete_event_confirmation_without_state_does_not_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    delete_event_mock = Mock()
    monkeypatch.setattr(
        event_deletion,
        "get_tool_payload",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        event_deletion,
        "delete_calendar_event",
        delete_event_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={"confirmed": True},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "missing_pending_event_delete"
    delete_event_mock.assert_not_called()


def test_delete_event_allows_one_time_all_day_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_common_dependencies(monkeypatch)
    monkeypatch.setattr(
        event_deletion,
        "search_calendar_events",
        Mock(return_value={"items": [_all_day_event()]}),
    )
    monkeypatch.setattr(
        event_deletion,
        "get_calendar_event",
        Mock(return_value=_all_day_event()),
    )
    monkeypatch.setattr(
        event_deletion,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={
            "confirmed": False,
            "title": "Día de planeación",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["pending_event"]["all_day"] is True


def test_delete_event_rejects_recurring_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recurring_event = _timed_event() | {
        "recurringEventId": "series-1"
    }
    _patch_common_dependencies(monkeypatch)
    monkeypatch.setattr(
        event_deletion,
        "search_calendar_events",
        Mock(return_value={"items": [recurring_event]}),
    )
    get_event_mock = Mock()
    monkeypatch.setattr(
        event_deletion,
        "get_calendar_event",
        get_event_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_delete_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "recurring_event_delete_not_supported"
    get_event_mock.assert_not_called()


def test_delete_event_intent_and_context_cover_safe_stages() -> None:
    prompt = build_tool_intent_prompt()
    intent = parse_tool_intent_response(
        """
        {
          "needs_tool": true,
          "tool_name": "calendar_delete_event",
          "arguments": {"confirmed": true}
        }
        """
    )
    selection_context = build_tool_context(
        "calendar_delete_event",
        {
            "success": False,
            "requires_selection": True,
        },
    )
    confirmation_context = build_tool_context(
        "calendar_delete_event",
        {
            "success": False,
            "requires_confirmation": True,
        },
    )
    success_context = build_tool_context(
        "calendar_delete_event",
        {"success": True},
    )

    assert "For calendar_delete_event:" in prompt
    assert intent.tool_name == "calendar_delete_event"
    assert "no event has been deleted" in selection_context
    assert "has not been deleted" in confirmation_context
    assert "deleted successfully" in success_context
