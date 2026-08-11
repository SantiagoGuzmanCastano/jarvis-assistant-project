from unittest.mock import Mock

import pytest

from app.schemas.tools.calendar import CalendarUpdateEventArguments
from app.schemas.tools.calendar_results import CalendarUpdateEventResult
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.intent_router import build_tool_intent_prompt
from app.services.intent_router_parser import parse_tool_intent_response
from app.services.tool_execution import (
    build_tool_context,
    tool_execution_system,
)
from app.tools.external.calendar import event_updates
from app.tools.registry import TOOLS


def _provider_event(
    *,
    event_id: str = "event-1",
    title: str = "Reunión Jarvis",
    start: str = "2026-08-01T10:00:00-05:00",
    end: str = "2026-08-01T11:00:00-05:00",
) -> dict:
    return {
        "id": event_id,
        "status": "confirmed",
        "summary": title,
        "description": "Revisar backend",
        "location": "Meet",
        "start": {
            "dateTime": start,
            "timeZone": "America/Bogota",
        },
        "end": {
            "dateTime": end,
            "timeZone": "America/Bogota",
        },
        "htmlLink": f"https://calendar.google.com/event?eid={event_id}",
    }


def test_update_event_is_registered_as_stateful_calendar_tool() -> None:
    definition = TOOLS["calendar_update_event"]

    assert definition["arguments_schema"] is CalendarUpdateEventArguments
    assert definition["result_schema"] is CalendarUpdateEventResult
    assert definition["requires_conversation_id"] is True
    assert "calendar_update_event" in CALENDAR_TOOL_NAMES


def test_update_event_prepares_single_match_without_patching(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    create_state_mock = Mock()
    patch_mock = Mock()
    monkeypatch.setattr(
        event_updates,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_updates,
        "search_calendar_events",
        Mock(return_value={"items": [_provider_event()]}),
    )
    monkeypatch.setattr(
        event_updates,
        "get_calendar_event",
        Mock(return_value=_provider_event()),
    )
    monkeypatch.setattr(
        event_updates,
        "create_tool_state",
        create_state_mock,
    )
    monkeypatch.setattr(
        event_updates,
        "patch_calendar_event",
        patch_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_update_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
            "new_title": "Revisión Phase 9",
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["requires_confirmation"] is True
    assert result["pending_update"]["updated_fields"] == ["title"]
    assert (
        result["pending_update"]["current_event"]["title"]
        == "Reunión Jarvis"
    )
    assert (
        result["pending_update"]["proposed_event"]["title"]
        == "Revisión Phase 9"
    )
    assert (
        result["pending_update"]["proposed_event"]["description"]
        == "Revisar backend"
    )
    assert (
        result["pending_update"]["proposed_event"]["end_date"]
        == "2026-08-01T11:00:00-05:00"
    )
    assert (
        result["pending_update"]["proposed_event"]["location"]
        == "Meet"
    )
    create_state_mock.assert_called_once()
    state_call = create_state_mock.call_args.kwargs
    assert (
        state_call["state_type"]
        == event_updates.CALENDAR_PENDING_EVENT_UPDATE_STATE
    )
    assert state_call["payload"]["changes"] == {
        "title": "Revisión Phase 9"
    }
    patch_mock.assert_not_called()


def test_update_event_preserves_candidates_for_exact_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    create_state_mock = Mock()
    get_event_mock = Mock()
    monkeypatch.setattr(
        event_updates,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_updates,
        "search_calendar_events",
        Mock(
            return_value={
                "items": [
                    _provider_event(event_id="cancelled", title="Cancelado")
                    | {"status": "cancelled"},
                    _provider_event(event_id="event-1"),
                    _provider_event(
                        event_id="event-2",
                        title="Reunión Jarvis semanal",
                    ),
                ]
            }
        ),
    )
    monkeypatch.setattr(
        event_updates,
        "get_calendar_event",
        get_event_mock,
    )
    monkeypatch.setattr(
        event_updates,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_update_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
            "new_location": "Sala 4",
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["requires_selection"] is True
    assert result["returned_count"] == 2
    assert [
        event["position"] for event in result["matching_events"]
    ] == [1, 2]
    state_payload = create_state_mock.call_args.kwargs["payload"]
    assert state_payload["changes"] == {"location": "Sala 4"}
    assert [event["event_id"] for event in state_payload["events"]] == [
        "event-1",
        "event-2",
    ]
    get_event_mock.assert_not_called()


def test_update_event_uses_saved_candidate_and_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    create_state_mock = Mock()
    get_event_mock = Mock(return_value=_provider_event(event_id="event-2"))
    monkeypatch.setattr(
        event_updates,
        "get_tool_payload",
        Mock(
            return_value={
                "events": [
                    {
                        "event_id": "event-1",
                        "is_recurring": False,
                    },
                    {
                        "event_id": "event-2",
                        "is_recurring": False,
                    },
                ],
                "changes": {"location": "Sala 4"},
                "calendar_id": "primary",
                "timezone": "America/Bogota",
            }
        ),
    )
    monkeypatch.setattr(
        event_updates,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_updates,
        "get_calendar_event",
        get_event_mock,
    )
    monkeypatch.setattr(
        event_updates,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_update_event",
        arguments={
            "confirmed": False,
            "selected_result_position": 2,
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["pending_update"]["proposed_event"]["location"] == "Sala 4"
    get_event_mock.assert_called_once_with(
        access_token="access-token",
        calendar_id="primary",
        event_id="event-2",
        timezone="America/Bogota",
    )


def test_update_event_confirmation_applies_saved_patch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    delete_state_mock = Mock()
    pending_update = {
        "event_id": "event-1",
        "calendar_id": "primary",
        "timezone": "America/Bogota",
        "changes": {
            "title": "Revisión Phase 9",
            "start_date": "2026-08-01T14:00:00-05:00",
            "end_date": "2026-08-01T15:00:00-05:00",
        },
        "updated_fields": ["title", "start_date", "end_date"],
        "current_event": {},
        "proposed_event": {},
    }
    updated_provider_event = _provider_event(
        title="Revisión Phase 9",
        start="2026-08-01T14:00:00-05:00",
        end="2026-08-01T15:00:00-05:00",
    )
    monkeypatch.setattr(
        event_updates,
        "get_tool_payload",
        Mock(return_value=pending_update),
    )
    monkeypatch.setattr(
        event_updates,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    patch_mock = Mock(return_value=updated_provider_event)
    monkeypatch.setattr(
        event_updates,
        "patch_calendar_event",
        patch_mock,
    )
    monkeypatch.setattr(
        event_updates,
        "delete_tool_state",
        delete_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_update_event",
        arguments={"confirmed": True},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["updated_fields"] == [
        "title",
        "start_date",
        "end_date",
    ]
    assert result["event"]["title"] == "Revisión Phase 9"
    patch_mock.assert_called_once_with(
        access_token="access-token",
        calendar_id="primary",
        event_id="event-1",
        timezone="America/Bogota",
        changes=pending_update["changes"],
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


def test_update_event_rejects_invalid_merged_range_without_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_updates,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_updates,
        "search_calendar_events",
        Mock(return_value={"items": [_provider_event()]}),
    )
    monkeypatch.setattr(
        event_updates,
        "get_calendar_event",
        Mock(return_value=_provider_event()),
    )
    monkeypatch.setattr(
        event_updates,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_update_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
            "new_start_date": "2026-08-01T12:00:00-05:00",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "invalid_proposed_event_range"
    create_state_mock.assert_not_called()


def test_update_event_intent_and_context_cover_all_safe_stages() -> None:
    prompt = build_tool_intent_prompt()
    intent = parse_tool_intent_response(
        """
        {
          "needs_tool": true,
          "tool_name": "calendar_update_event",
          "arguments": {"confirmed": true}
        }
        """
    )
    selection_context = build_tool_context(
        "calendar_update_event",
        {
            "success": False,
            "requires_selection": True,
            "matching_events": [],
        },
    )
    confirmation_context = build_tool_context(
        "calendar_update_event",
        {
            "success": False,
            "requires_confirmation": True,
        },
    )
    success_context = build_tool_context(
        "calendar_update_event",
        {"success": True},
    )

    assert "For calendar_update_event:" in prompt
    assert intent.tool_name == "calendar_update_event"
    assert "no event has been updated" in selection_context
    assert "has not been modified yet" in confirmation_context
    assert "updated successfully" in success_context
