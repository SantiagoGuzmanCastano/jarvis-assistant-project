from datetime import datetime
from unittest.mock import Mock, call
from zoneinfo import ZoneInfo

import pytest

from app.schemas.tools.calendar import (
    CalendarPrepareEventFromEmailArguments,
)
from app.schemas.tools.calendar_results import (
    CalendarPrepareEventFromEmailResult,
)
from app.services.calendar_event_extraction import ExtractedCalendarEvent
from app.services.chat import CALENDAR_TOOL_NAMES
from app.services.intent_router import build_tool_intent_prompt
from app.services.tool_execution import (
    build_tool_context,
    tool_execution_system,
)
from app.tools.external.calendar import (
    event_creation,
    event_preparation_from_email,
)
from app.tools.registry import TOOLS


BOGOTA = ZoneInfo("America/Bogota")


def _complete_extraction() -> ExtractedCalendarEvent:
    return ExtractedCalendarEvent(
        title="Reunión Jarvis",
        description="Revisar Phase 9",
        start_date=datetime(2026, 7, 31, 10, tzinfo=BOGOTA),
        end_date=datetime(2026, 7, 31, 11, tzinfo=BOGOTA),
        location="Meet",
    )


def _raw_email(message_id: str, subject: str) -> dict:
    return {
        "id": message_id,
        "threadId": f"thread-{message_id}",
        "snippet": "Meeting details",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "ana@example.com"},
                {"name": "To", "value": "lina@example.com"},
                {"name": "Subject", "value": subject},
                {
                    "name": "Date",
                    "value": "Wed, 29 Jul 2026 10:00:00 -0500",
                },
            ],
            "body": {"data": "TWVldGluZyBmcm9tIDEwIHRvIDExLg=="},
        },
    }


def _draft_summary(draft_id: str, subject: str) -> dict:
    return {
        "position": 1,
        "draft_id": draft_id,
        "to": "ana@example.com",
        "subject": subject,
        "date": "2026-07-29",
        "snippet": "Meeting details",
    }


def test_prepare_event_from_email_is_registered_as_stateful_tool() -> None:
    definition = TOOLS["calendar_prepare_event_from_email"]

    assert (
        definition["arguments_schema"]
        is CalendarPrepareEventFromEmailArguments
    )
    assert (
        definition["result_schema"]
        is CalendarPrepareEventFromEmailResult
    )
    assert definition["requires_conversation_id"] is True
    assert "calendar_prepare_event_from_email" in CALENDAR_TOOL_NAMES


def test_active_email_fetches_exact_full_message_before_extraction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    get_payload_mock = Mock(
        return_value={
            "active_email": {
                "message_id": "message-1",
                "thread_id": "thread-1",
                "source": "received",
            }
        }
    )
    fetch_message_mock = Mock(
        return_value={
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {
                        "name": "Subject",
                        "value": "Reunión Jarvis",
                    }
                ],
                "body": {"data": "UmV1bmnDs24="},
            }
        }
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        get_payload_mock,
    )
    token_mock = Mock(return_value="access-token")
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        token_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_message_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "active",
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["requires_confirmation"] is True
    token_mock.assert_called_once_with(user_id=7, session=session)
    fetch_message_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-1",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["source_type"]
        == "email"
    )
    assert (
        create_state_mock.call_args.kwargs["state_type"]
        == event_creation.CALENDAR_PENDING_EVENT_CREATION_STATE
    )


def test_active_draft_uses_saved_payload_without_gmail_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_payload_mock = Mock(
        return_value={
            "active_draft": {
                "draft_id": "draft-1",
                "to": "ana@example.com",
                "subject": "Reunión Jarvis",
                "body": "Reunión mañana de 10 a 11.",
            }
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        get_payload_mock,
    )
    token_mock = Mock()
    fetch_message_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        token_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_message_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "active",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert (
        extractor_mock.call_args.kwargs["source_content"]["body"]
        == "Reunión mañana de 10 a 11."
    )
    token_mock.assert_not_called()
    fetch_message_mock.assert_not_called()


def test_incomplete_extraction_preserves_partial_pending_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(
            return_value={
                "active_draft": {
                    "draft_id": "draft-1",
                    "to": "ana@example.com",
                    "subject": "Reunión Jarvis",
                    "body": "Reunión mañana a las 10.",
                }
            }
        ),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        Mock(
            return_value=ExtractedCalendarEvent(
                title="Reunión Jarvis",
                start_date=datetime(
                    2026,
                    7,
                    31,
                    10,
                    tzinfo=BOGOTA,
                ),
                end_date=None,
            )
        ),
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "active",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_details"] is True
    assert result["missing_fields"] == ["end_date"]
    assert (
        create_state_mock.call_args.kwargs["payload"]["pending_event"][
            "start_date"
        ]
        == "2026-07-31T10:00:00-05:00"
    )


def test_recent_email_uses_requested_recent_position(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = Mock()
    token_mock = Mock(return_value="access-token")
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        token_mock,
    )
    messages = [
        {
            "id": "message-1",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Latest meeting"}
                ],
                "body": {"data": "TGF0ZXN0"},
            },
        },
        {
            "id": "message-2",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {
                        "name": "Subject",
                        "value": "Penultimate meeting",
                    }
                ],
                "body": {"data": "UGVudWx0aW1hdGU="},
            },
        },
    ]
    fetch_recent_mock = Mock(return_value=messages)
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_latest_gmail_messages",
        fetch_recent_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "recent",
            "recent_result_position": 2,
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_recent_mock.assert_called_once_with(
        access_token="access-token",
        max_results=2,
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Penultimate meeting"
    )


def test_recent_draft_uses_requested_recent_position(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_recent_mock = Mock(
        return_value={
            "drafts": [
                _draft_summary("draft-1", "Latest meeting"),
                {
                    **_draft_summary(
                        "draft-2",
                        "Penultimate meeting",
                    ),
                    "position": 2,
                },
            ]
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_drafts",
        fetch_recent_mock,
    )
    fetch_full_mock = Mock(return_value={"id": "draft-2"})
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_gmail_draft_full",
        fetch_full_mock,
    )
    format_mock = Mock(
        return_value={
            **_draft_summary("draft-2", "Penultimate meeting"),
            "position": 2,
            "body": "Meeting tomorrow from 10 to 11.",
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "format_gmail_draft_full",
        format_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "recent",
            "recent_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_recent_mock.assert_called_once_with(
        access_token="access-token",
        max_results=2,
        query="",
    )
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-2",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["body"]
        == "Meeting tomorrow from 10 to 11."
    )


def test_search_with_multiple_emails_saves_only_candidate_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    search_mock = Mock(
        return_value={
            "emails": [
                {
                    "message_id": "message-1",
                    "thread_id": "thread-1",
                    "sender": "ana@example.com",
                    "subject": "Meeting one",
                    "date": "2026-07-30",
                    "snippet": "First candidate",
                },
                {
                    "message_id": "message-2",
                    "thread_id": "thread-2",
                    "sender": "ana@example.com",
                    "subject": "Meeting two",
                    "date": "2026-07-31",
                    "snippet": "Second candidate",
                },
            ],
            "returned_count": 2,
            "has_more": False,
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_message_format_FSD",
        search_mock,
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )
    extractor_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "search",
            "sender_hint": ["Ana"],
            "search_keywords": ["meeting"],
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_selection"] is True
    assert result["returned_count"] == 2
    state_call = create_state_mock.call_args.kwargs
    assert (
        state_call["state_type"]
        == event_preparation_from_email.CALENDAR_GMAIL_SOURCE_SELECTION_STATE
    )
    assert all(
        "body" not in candidate
        for candidate in state_call["payload"]["candidates"]
    )
    assert result["matching_sources"][0]["contact"] == "ana@example.com"
    extractor_mock.assert_not_called()


def test_search_with_multiple_drafts_saves_only_candidate_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_drafts",
        Mock(
            return_value={
                "drafts": [
                    _draft_summary("draft-1", "Meeting one"),
                    {
                        **_draft_summary("draft-2", "Meeting two"),
                        "position": 2,
                    },
                ],
                "returned_count": 2,
                "has_more": False,
            }
        ),
    )
    create_state_mock = Mock()
    extractor_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "search",
            "recipient_hint": ["Ana"],
            "search_keywords": ["meeting"],
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_selection"] is True
    assert result["returned_count"] == 2
    state_payload = create_state_mock.call_args.kwargs["payload"]
    assert state_payload["source_type"] == "draft"
    assert all(
        "body" not in candidate
        for candidate in state_payload["candidates"]
    )
    extractor_mock.assert_not_called()


def test_search_with_single_email_fetches_exact_content_and_extracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_message_format_FSD",
        Mock(
            return_value={
                "emails": [
                    {
                        "message_id": "message-1",
                        "thread_id": "thread-1",
                        "sender": "ana@example.com",
                        "subject": "Selected meeting",
                        "date": "2026-07-29",
                        "snippet": "Meeting details",
                    }
                ],
                "returned_count": 1,
                "has_more": False,
            }
        ),
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("message-1", "Selected meeting")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "search",
            "sender_hint": ["Ana"],
            "search_keywords": ["meeting"],
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-1",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Selected meeting"
    )


def test_search_with_single_draft_fetches_exact_content_and_extracts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_drafts",
        Mock(
            return_value={
                "drafts": [
                    _draft_summary("draft-1", "Selected meeting")
                ],
                "returned_count": 1,
                "has_more": False,
            }
        ),
    )
    fetch_full_mock = Mock(return_value={"id": "draft-1"})
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_gmail_draft_full",
        fetch_full_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "format_gmail_draft_full",
        Mock(
            return_value={
                **_draft_summary(
                    "draft-1",
                    "Selected meeting",
                ),
                "body": "Meeting tomorrow from 10 to 11.",
            }
        ),
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "search",
            "recipient_hint": ["Ana"],
            "search_keywords": ["meeting"],
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-1",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["body"]
        == "Meeting tomorrow from 10 to 11."
    )


@pytest.mark.parametrize("source_type", ["email", "draft"])
def test_search_without_results_does_not_extract(
    source_type: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_message_format_FSD",
        Mock(
            return_value={
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }
        ),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_gmail_drafts",
        Mock(
            return_value={
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }
        ),
    )
    extractor_mock = Mock()
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )
    contact_arguments = (
        {"sender_hint": ["Ana"]}
        if source_type == "email"
        else {"recipient_hint": ["Ana"]}
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": source_type,
            "selection_source": "search",
            **contact_arguments,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "no_matching_gmail_source"
    extractor_mock.assert_not_called()
    create_state_mock.assert_not_called()


def test_previous_draft_selection_fetches_only_selected_full_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(
            return_value={
                "source_type": "draft",
                "candidates": [
                    {
                        "position": 1,
                        "source_type": "draft",
                        "source_id": "draft-1",
                    },
                    {
                        "position": 2,
                        "source_type": "draft",
                        "source_id": "draft-2",
                    },
                ],
            }
        ),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_draft_mock = Mock(return_value={"id": "draft-2"})
    format_draft_mock = Mock(
        return_value={
            "position": 2,
            "draft_id": "draft-2",
            "to": "ana@example.com",
            "subject": "Selected meeting",
            "date": "2026-07-31",
            "snippet": "Selected",
            "body": "Meeting tomorrow from 10 to 11.",
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_gmail_draft_full",
        fetch_draft_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "format_gmail_draft_full",
        format_draft_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "previous_selection",
            "selected_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_draft_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-2",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["body"]
        == "Meeting tomorrow from 10 to 11."
    )


def test_previous_email_selection_fetches_only_selected_full_email(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(
            return_value={
                "source_type": "email",
                "candidates": [
                    {
                        "position": 1,
                        "source_type": "email",
                        "source_id": "message-1",
                    },
                    {
                        "position": 2,
                        "source_type": "email",
                        "source_id": "message-2",
                    },
                ],
            }
        ),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("message-2", "Selected meeting")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "previous_selection",
            "selected_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-2",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Selected meeting"
    )


def test_previous_selection_reuses_gmail_draft_selection_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    drafts = [
        {
            "position": 1,
            "draft_id": "draft-september-20",
            "to": "recipient@example.com",
            "subject": "Reunión de septiembre - Propuesta 3",
            "date": "2026-07-29T12:09:05-05:00",
            "snippet": "Propuesta de reunión para el día 20.",
        },
        {
            "position": 2,
            "draft_id": "draft-september-12",
            "to": "recipient@example.com",
            "subject": "Reunión de septiembre - Propuesta 2",
            "date": "2026-07-29T12:08:05-05:00",
            "snippet": "Propuesta de reunión para el día 12.",
        },
    ]

    def get_payload_by_state_type(**kwargs):
        if kwargs["state_type"] == "gmail_draft_selection":
            return {"drafts": drafts}
        return None

    get_payload_mock = Mock(side_effect=get_payload_by_state_type)
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        get_payload_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_full_mock = Mock(
        return_value={"id": "draft-september-20"}
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_gmail_draft_full",
        fetch_full_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "format_gmail_draft_full",
        Mock(
            return_value={
                **drafts[0],
                "body": (
                    "Reunión el 20 de septiembre "
                    "de 11:05 a 12:50."
                ),
            }
        ),
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "draft",
            "selection_source": "previous_selection",
            "selected_result_position": 1,
        },
        user_id=7,
        session=Mock(),
        conversation_id=196,
    )

    assert result["requires_confirmation"] is True
    assert [
        call.kwargs["state_type"]
        for call in get_payload_mock.call_args_list
    ] == [
        event_preparation_from_email.CALENDAR_GMAIL_SOURCE_SELECTION_STATE,
        "gmail_draft_selection",
    ]
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-september-20",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Reunión de septiembre - Propuesta 3"
    )


def test_previous_selection_reuses_gmail_email_selection_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emails = [
        {
            "position": 1,
            "message_id": "message-1",
            "thread_id": "thread-1",
            "sender": "ana@example.com",
            "subject": "Meeting one",
            "date": "2026-07-29",
            "snippet": "First meeting",
        },
        {
            "position": 2,
            "message_id": "message-2",
            "thread_id": "thread-2",
            "sender": "ana@example.com",
            "subject": "Meeting two",
            "date": "2026-07-29",
            "snippet": "Second meeting",
        },
    ]

    def get_payload_by_state_type(**kwargs):
        if kwargs["state_type"] == "gmail_email_selection":
            return {"emails": emails}
        return None

    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(side_effect=get_payload_by_state_type),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("message-2", "Meeting two")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "previous_selection",
            "selected_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=196,
    )

    assert result["requires_confirmation"] is True
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-2",
    )
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Meeting two"
    )


def test_active_sent_email_requires_sent_active_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(
            return_value={
                "active_email": {
                    "message_id": "sent-1",
                    "thread_id": "thread-sent-1",
                    "source": "sent",
                }
            }
        ),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("sent-1", "Sent meeting")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "sent_email",
            "selection_source": "active",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["source_type"] == "sent_email"
    assert (
        extractor_mock.call_args.kwargs["source_content"]["source_type"]
        == "sent_email"
    )
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="sent-1",
    )


def test_recent_sent_email_uses_requested_position(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_sent_mock = Mock(
        return_value={
            "emails": [
                {
                    "message_id": "sent-1",
                    "thread_id": "thread-sent-1",
                    "recipient": "ana@example.com",
                    "subject": "First sent meeting",
                    "date": "2026-07-29",
                    "snippet": "First",
                },
                {
                    "message_id": "sent-2",
                    "thread_id": "thread-sent-2",
                    "recipient": "ana@example.com",
                    "subject": "Second sent meeting",
                    "date": "2026-07-28",
                    "snippet": "Second",
                },
            ],
            "returned_count": 2,
            "has_more": False,
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_sent_gmail_messages",
        fetch_sent_mock,
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("sent-2", "Second sent meeting")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        Mock(return_value=_complete_extraction()),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "sent_email",
            "selection_source": "recent",
            "recent_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    fetch_sent_mock.assert_called_once_with(
        access_token="access-token",
        max_results=2,
    )
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="sent-2",
    )


def test_search_with_multiple_sent_emails_requests_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    search_mock = Mock(
        return_value={
            "emails": [
                {
                    "message_id": "sent-1",
                    "thread_id": "thread-sent-1",
                    "recipient": "ana@example.com",
                    "subject": "Meeting one",
                    "date": "2026-07-29",
                    "snippet": "First",
                },
                {
                    "message_id": "sent-2",
                    "thread_id": "thread-sent-2",
                    "recipient": "ana@example.com",
                    "subject": "Meeting two",
                    "date": "2026-07-28",
                    "snippet": "Second",
                },
            ],
            "returned_count": 2,
            "has_more": False,
        }
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_specific_sent_gmail_messages",
        search_mock,
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )
    extractor_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "sent_email",
            "selection_source": "search",
            "recipient_hint": ["Ana"],
            "search_keywords": ["meeting"],
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_selection"] is True
    assert result["source_type"] == "sent_email"
    assert result["matching_sources"][0]["contact"] == "ana@example.com"
    state_payload = create_state_mock.call_args.kwargs["payload"]
    assert state_payload["source_type"] == "sent_email"
    assert all(
        candidate["source_type"] == "sent_email"
        for candidate in state_payload["candidates"]
    )
    extractor_mock.assert_not_called()


def test_previous_selection_reuses_sent_email_selection_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_emails = [
        {
            "position": 1,
            "message_id": "sent-1",
            "thread_id": "thread-sent-1",
            "recipient": "ana@example.com",
            "subject": "Meeting one",
            "date": "2026-07-29",
            "snippet": "First",
        },
        {
            "position": 2,
            "message_id": "sent-2",
            "thread_id": "thread-sent-2",
            "recipient": "ana@example.com",
            "subject": "Meeting two",
            "date": "2026-07-28",
            "snippet": "Second",
        },
    ]

    def get_payload_by_state_type(**kwargs):
        if kwargs["state_type"] == "gmail_sent_email_selection":
            return {"emails": sent_emails}
        return None

    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(side_effect=get_payload_by_state_type),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    fetch_full_mock = Mock(
        return_value=_raw_email("sent-2", "Meeting two")
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        fetch_full_mock,
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        Mock(return_value=_complete_extraction()),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        Mock(),
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "sent_email",
            "selection_source": "previous_selection",
            "selected_result_position": 2,
        },
        user_id=7,
        session=Mock(),
        conversation_id=196,
    )

    assert result["requires_confirmation"] is True
    fetch_full_mock.assert_called_once_with(
        access_token="access-token",
        message_id="sent-2",
    )


def test_explicit_event_overrides_take_priority_over_email_extraction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email_selection = {
        "emails": [
            {
                "position": 1,
                "message_id": "message-1",
                "thread_id": "thread-1",
                "sender": "ana@example.com",
                "subject": "Original meeting title",
                "date": "2026-07-29",
                "snippet": "Meeting details",
            }
        ]
    }

    def get_payload_by_state_type(**kwargs):
        if kwargs["state_type"] == "gmail_email_selection":
            return email_selection
        return None

    monkeypatch.setattr(
        event_preparation_from_email,
        "get_tool_payload",
        Mock(side_effect=get_payload_by_state_type),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "get_valid_google_access_token",
        Mock(return_value="access-token"),
    )
    monkeypatch.setattr(
        event_preparation_from_email,
        "fetch_full_specific_gmail_messages_metadata",
        Mock(return_value=_raw_email("message-1", "Original title")),
    )
    extractor_mock = Mock(return_value=_complete_extraction())
    monkeypatch.setattr(
        event_preparation_from_email,
        "extract_calendar_event_from_gmail_content",
        extractor_mock,
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_preparation_from_email,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_prepare_event_from_email",
        arguments={
            "source_type": "email",
            "selection_source": "previous_selection",
            "selected_result_position": 1,
            "event_title": "Reunion charla importante!!",
            "event_description": "Descripción elegida por el usuario",
            "event_start_date": "2026-09-28T08:00:00-05:00",
            "event_end_date": "2026-09-28T09:30:00-05:00",
            "event_location": "Sala principal",
        },
        user_id=7,
        session=Mock(),
        conversation_id=196,
    )

    proposal = result["extracted_event"]
    assert proposal["title"] == "Reunion charla importante!!"
    assert proposal["description"] == "Descripción elegida por el usuario"
    assert proposal["start_date"] == "2026-09-28T08:00:00-05:00"
    assert proposal["end_date"] == "2026-09-28T09:30:00-05:00"
    assert proposal["location"] == "Sala principal"
    pending_event = create_state_mock.call_args.kwargs["payload"][
        "pending_event"
    ]
    assert pending_event == proposal
    assert (
        extractor_mock.call_args.kwargs["source_content"]["subject"]
        == "Original title"
    )


def test_create_event_completes_existing_extracted_proposal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending_event = {
        "title": "Reunión Jarvis",
        "description": "Revisar Phase 9",
        "start_date": "2026-07-31T10:00:00-05:00",
        "end_date": None,
        "timezone": "America/Bogota",
        "calendar_id": "primary",
        "location": "Meet",
    }
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value={"pending_event": pending_event}),
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={
            "confirmed": False,
            "end_date": "2026-07-31T11:00:00-05:00",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["pending_event"]["title"] == "Reunión Jarvis"
    assert result["pending_event"]["location"] == "Meet"
    assert (
        result["pending_event"]["end_date"]
        == "2026-07-31T11:00:00-05:00"
    )


def test_create_event_merges_follow_up_fields_into_email_proposal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pending_event = {
        "title": "Te dicen algo bonito. Y tú lo destrozas.",
        "description": None,
        "start_date": None,
        "end_date": None,
        "timezone": "America/Bogota",
        "calendar_id": "primary",
        "location": None,
    }
    monkeypatch.setattr(
        event_creation,
        "get_tool_payload",
        Mock(return_value={"pending_event": pending_event}),
    )
    create_state_mock = Mock()
    monkeypatch.setattr(
        event_creation,
        "create_tool_state",
        create_state_mock,
    )

    result = tool_execution_system(
        tool_name="calendar_create_event",
        arguments={
            "confirmed": False,
            "description": "Reunión importante de mi mentor Adrià",
            "start_date": "2026-07-29T13:00:00-05:00",
            "end_date": "2026-07-29T16:00:00-05:00",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["requires_confirmation"] is True
    assert result["pending_event"] == {
        **pending_event,
        "description": "Reunión importante de mi mentor Adrià",
        "start_date": "2026-07-29T13:00:00-05:00",
        "end_date": "2026-07-29T16:00:00-05:00",
    }
    assert (
        create_state_mock.call_args.kwargs["payload"]["pending_event"]
        == result["pending_event"]
    )


def test_prepare_event_intent_and_context_explain_non_mutation() -> None:
    prompt = build_tool_intent_prompt()
    context = build_tool_context(
        "calendar_prepare_event_from_email",
        {
            "success": True,
            "requires_details": True,
            "missing_fields": ["end_date"],
        },
    )

    assert "For calendar_prepare_event_from_email:" in prompt
    assert "no Calendar event was created" in context
    assert "Ask only for the fields listed in missing_fields" in context

    selection_context = build_tool_context(
        "calendar_prepare_event_from_email",
        {
            "success": False,
            "requires_selection": True,
            "matching_sources": [{"position": 1}],
        },
    )
    assert "no Calendar event was created or prepared" in selection_context
