from unittest.mock import Mock

from app.schemas.tools.calendar import CalendarCreateEventArguments
from app.schemas.tools.calendar_results import CalendarCreateEventResult
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.tool_execution import build_tool_context, tool_execution_system
from app.tools.external.calendar import event_creation
from app.tools.registry import TOOLS


PENDING_EVENT = {
    "title": "Reunión Jarvis",
    "description": "Revisar el MVP",
    "start_date": "2026-08-01T10:00:00-05:00",
    "end_date": "2026-08-01T11:00:00-05:00",
    "location": "Sala principal",
    "calendar_id": "primary",
    "timezone": "America/Bogota",
}


def test_create_event_is_registered_as_stateful_calendar_tool() -> None:
    definition = TOOLS["calendar_create_event"]

    assert definition["arguments_schema"] is CalendarCreateEventArguments
    assert definition["result_schema"] is CalendarCreateEventResult
    assert definition["requires_conversation_id"] is True
    assert "calendar_create_event" in CALENDAR_TOOL_NAMES


def test_create_event_prepares_explicit_fields_without_mutating_calendar(
    monkeypatch,
) -> None:
    create_state_mock = Mock()
    access_token_mock = Mock()
    provider_create_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        event_creation,
        "create_tool_state",
        create_state_mock,
    )
    monkeypatch.setattr(
        event_creation,
        "get_valid_google_access_token",
        access_token_mock,
    )
    monkeypatch.setattr(
        event_creation,
        "create_calendar_event",
        provider_create_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={"confirmed": False, **PENDING_EVENT},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["requires_confirmation"] is True
    assert result["pending_event"] == PENDING_EVENT
    state_call = create_state_mock.call_args.kwargs
    assert (
        state_call["state_type"]
        == event_creation.CALENDAR_PENDING_EVENT_CREATION_STATE
    )
    assert state_call["payload"] == {"pending_event": PENDING_EVENT}
    access_token_mock.assert_not_called()
    provider_create_mock.assert_not_called()


def test_create_event_preserves_incomplete_proposal_for_follow_up(
    monkeypatch,
) -> None:
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        event_creation,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={
            "confirmed": False,
            "title": "Reunión Jarvis",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result == {
        "success": False,
        "requires_confirmation": False,
        "reason": "missing_required_fields",
        "message": "Title, start date, and end date are required.",
        "missing_fields": ["start_date", "end_date"],
        "pending_event": None,
        "event": None,
    }
    saved_event = create_state_mock.call_args.kwargs["payload"][
        "pending_event"
    ]
    assert saved_event["title"] == "Reunión Jarvis"
    assert saved_event["start_date"] is None
    assert saved_event["end_date"] is None


def test_create_event_confirmation_requires_pending_state(
    monkeypatch,
) -> None:
    provider_create_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value=None),
    )
    monkeypatch.setattr(
        event_creation,
        "create_calendar_event",
        provider_create_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={"confirmed": True},
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "missing_pending_event"
    provider_create_mock.assert_not_called()


def test_create_event_confirmation_creates_exact_pending_event(
    monkeypatch,
) -> None:
    session = Mock()
    access_token_mock = Mock(return_value="access-token")
    provider_create_mock = Mock(
        return_value={
            "id": "event-1",
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
            "htmlLink": "https://calendar.google.com/event?eid=event-1",
        }
    )
    delete_state_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value={"pending_event": PENDING_EVENT}),
    )
    monkeypatch.setattr(
        event_creation,
        "get_valid_google_access_token",
        access_token_mock,
    )
    monkeypatch.setattr(
        event_creation,
        "create_calendar_event",
        provider_create_mock,
    )
    monkeypatch.setattr(
        event_creation,
        "delete_tool_state",
        delete_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={"confirmed": True},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["requires_confirmation"] is False
    assert result["event"] == {
        "event_id": "event-1",
        **PENDING_EVENT,
        "html_link": "https://calendar.google.com/event?eid=event-1",
    }
    access_token_mock.assert_called_once_with(user_id=7, session=session)
    provider_create_mock.assert_called_once_with(
        title=PENDING_EVENT["title"],
        description=PENDING_EVENT["description"],
        start_date=PENDING_EVENT["start_date"],
        end_date=PENDING_EVENT["end_date"],
        access_token="access-token",
        calendar_id="primary",
        timezone="America/Bogota",
        location="Sala principal",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


def test_create_event_context_preserves_confirmation_boundary() -> None:
    pending_context = build_tool_context(
        "calendar_create_event",
        {
            "success": False,
            "requires_confirmation": True,
            "pending_event": PENDING_EVENT,
        },
    )
    created_context = build_tool_context(
        "calendar_create_event",
        {
            "success": True,
            "event": {
                "event_id": "event-1",
                **PENDING_EVENT,
                "html_link": "https://calendar.google.com/event?eid=event-1",
            },
        },
    )

    assert "has not been created yet" in pending_context
    assert "explicit confirmation" in pending_context
    assert "created in Google Calendar" in created_context

