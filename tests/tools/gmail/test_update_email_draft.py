from unittest.mock import Mock, call, patch

import pytest

from app.core.errors import AppError
from app.schemas.tools.gmail_results import UpdateDraftResult
from app.tools.external.gmail.draft_updates import (
    _update_and_verify_draft,
    gmail_update_email_draft_tool,
)


@patch("app.tools.external.gmail.draft_updates.create_tool_state")
@patch("app.tools.external.gmail.draft_updates.delete_tool_state")
@patch("app.tools.external.gmail.draft_updates._update_and_verify_draft")
@patch("app.tools.external.gmail.draft_updates.get_tool_payload")
@patch("app.tools.external.gmail.draft_updates.get_valid_google_access_token")
def test_active_draft_update_preserves_unspecified_fields(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    update_and_verify_mock: Mock,
    delete_state_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    active_draft = {
        "draft_id": "draft-1",
        "to": "lina@example.com",
        "subject": "Factura enero",
        "body": "Contenido original.",
    }
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = {"active_draft": active_draft}
    update_and_verify_mock.return_value = {
        **active_draft,
        "subject": "Factura enero corregida",
    }

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=session,
        arguments={
            "selection_source": "active",
            "new_subject": "Factura enero corregida",
        },
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["draft"]["to"] == "lina@example.com"
    assert result["draft"]["subject"] == "Factura enero corregida"
    assert result["draft"]["body"] == "Contenido original."
    validated_result = UpdateDraftResult.model_validate(result)
    assert validated_result.draft is not None
    assert validated_result.draft.draft_id == "draft-1"
    update_and_verify_mock.assert_called_once_with(
        access_token="access-token",
        draft=active_draft,
        body="Contenido original.",
        subject="Factura enero corregida",
        recipient_email="lina@example.com",
    )
    delete_state_mock.assert_not_called()
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_draft",
        payload={
            "active_draft": {
                **active_draft,
                "subject": "Factura enero corregida",
            }
        },
    )


@patch("app.tools.external.gmail.draft_updates.create_tool_state")
@patch("app.tools.external.gmail.draft_updates.delete_tool_state")
@patch("app.tools.external.gmail.draft_updates.fetch_specific_gmail_drafts_full")
@patch("app.tools.external.gmail.draft_updates.build_gmail_query", return_value="to:lina@example.com")
@patch("app.tools.external.gmail.draft_updates.get_valid_google_access_token")
def test_multiple_draft_update_search_saves_selection_state(
    access_token_mock: Mock,
    build_query_mock: Mock,
    fetch_drafts_mock: Mock,
    delete_state_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [
        {"draft_id": "draft-1", "to": "lina@example.com", "subject": "Factura enero", "body": "Uno"},
        {"draft_id": "draft-2", "to": "lina@example.com", "subject": "Factura febrero", "body": "Dos"},
    ]
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {"drafts": drafts}

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=session,
        arguments={
            "selection_source": "search",
            "recipient_hint": ["Lina"],
            "new_subject": "Factura corregida",
        },
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "multiple_matching_drafts"
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_update_draft_selection",
        payload={
            "drafts": drafts,
            "new_recipient_email": "",
            "new_subject": "Factura corregida",
            "new_body": "",
        },
    )


@patch("app.tools.external.gmail.draft_updates.create_tool_state")
@patch("app.tools.external.gmail.draft_updates._update_and_verify_draft")
@patch("app.tools.external.gmail.draft_updates.format_gmail_draft_full")
@patch("app.tools.external.gmail.draft_updates.fetch_gmail_draft_full")
@patch("app.tools.external.gmail.draft_updates.get_tool_payload")
@patch("app.tools.external.gmail.draft_updates.get_valid_google_access_token")
def test_generic_draft_selection_updates_the_selected_draft(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    fetch_full_draft_mock: Mock,
    format_draft_mock: Mock,
    update_and_verify_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    selected_draft = {
        "draft_id": "draft-2",
        "to": "lina@example.com",
        "subject": "Interés en Razer",
        "body": "Contenido original.",
    }
    selected_draft_summary = {
        "position": 2,
        "draft_id": "draft-2",
        "to": "lina@example.com",
        "subject": "Interés en Razer",
        "date": "2026-07-08T10:00:00-05:00",
        "snippet": "Contenido original.",
    }
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = {
        "drafts": [
            {
                "position": 1,
                "draft_id": "draft-1",
                "to": "lina@example.com",
                "subject": "Otro",
                "date": "2026-07-08T10:00:00-05:00",
                "snippet": "Uno",
            },
            selected_draft_summary,
        ]
    }
    fetch_full_draft_mock.return_value = {"id": "draft-2"}
    format_draft_mock.return_value = selected_draft
    update_and_verify_mock.return_value = {
        **selected_draft,
        "subject": "Rock progresivo",
    }

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=session,
        conversation_id=11,
        arguments={
            "selection_source": "search",
            "selected_result_position": 2,
            "new_subject": "Rock progresivo",
        },
    )

    assert result["success"] is True
    assert result["draft"]["subject"] == "Rock progresivo"
    fetch_full_draft_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-2",
    )
    update_and_verify_mock.assert_called_once_with(
        access_token="access-token",
        draft=selected_draft,
        body="Contenido original.",
        subject="Rock progresivo",
        recipient_email="lina@example.com",
    )
    get_payload_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_draft_selection",
    )
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_draft",
        payload={
            "active_draft": {
                **selected_draft,
                "subject": "Rock progresivo",
            }
        },
    )


@patch("app.tools.external.gmail.draft_updates._update_and_verify_draft")
@patch("app.tools.external.gmail.draft_updates.get_tool_payload")
@patch("app.tools.external.gmail.draft_updates.get_valid_google_access_token")
def test_generic_draft_selection_without_changes_requests_update_fields(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    update_and_verify_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = {
        "drafts": [
            {
                "draft_id": "draft-2",
                "to": "lina@example.com",
                "subject": "Interés en Razer",
                "body": "Contenido original.",
            }
        ]
    }

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=Mock(),
        conversation_id=11,
        arguments={
            "selection_source": "search",
            "selected_result_position": 1,
        },
    )

    assert result["success"] is False
    assert result["reason"] == "missing_update_fields"
    update_and_verify_mock.assert_not_called()


@patch("app.tools.external.gmail.draft_updates.create_tool_state")
@patch("app.tools.external.gmail.draft_updates._update_and_verify_draft")
@patch("app.tools.external.gmail.draft_updates.get_tool_payload")
@patch("app.tools.external.gmail.draft_updates.get_valid_google_access_token")
def test_update_selection_falls_back_to_legacy_pending_update_state(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    update_and_verify_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    selected_draft = {
        "draft_id": "draft-1",
        "to": "lina@example.com",
        "subject": "Factura",
        "body": "Contenido original.",
    }
    access_token_mock.return_value = "access-token"
    get_payload_mock.side_effect = [
        None,
        {"drafts": [selected_draft], "new_body": "Contenido corregido."},
    ]
    update_and_verify_mock.return_value = {
        **selected_draft,
        "body": "Contenido corregido.",
    }

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=session,
        conversation_id=11,
        arguments={
            "selection_source": "search",
            "selected_result_position": 1,
        },
    )

    assert result["success"] is True
    assert result["draft"]["body"] == "Contenido corregido."
    get_payload_mock.assert_has_calls(
        [
            call(
                user_id=7,
                conversation_id=11,
                session=session,
                state_type="gmail_draft_selection",
            ),
            call(
                user_id=7,
                conversation_id=11,
                session=session,
                state_type="gmail_update_draft_selection",
            ),
        ]
    )
    update_and_verify_mock.assert_called_once_with(
        access_token="access-token",
        draft=selected_draft,
        body="Contenido corregido.",
        subject="Factura",
        recipient_email="lina@example.com",
    )


@patch("app.tools.external.gmail.draft_updates.format_gmail_draft_full")
@patch("app.tools.external.gmail.draft_updates.fetch_gmail_draft_full")
@patch("app.tools.external.gmail.draft_updates.update_gmail_draft")
def test_update_verification_returns_the_refetched_draft(
    update_draft_mock: Mock,
    fetch_full_draft_mock: Mock,
    format_draft_mock: Mock,
) -> None:
    draft = {
        "position": 1,
        "draft_id": "draft-1",
        "to": "lina@example.com",
        "subject": "Factura",
        "body": "Contenido original.",
    }
    verified_draft = {
        **draft,
        "subject": "Factura corregida",
        "date": "2026-07-20T10:00:00-05:00",
        "snippet": "Contenido original.",
    }
    update_draft_mock.return_value = {"id": "draft-1"}
    fetch_full_draft_mock.return_value = {"id": "draft-1"}
    format_draft_mock.return_value = verified_draft

    result = _update_and_verify_draft(
        access_token="access-token",
        draft=draft,
        recipient_email="lina@example.com",
        subject="Factura corregida",
        body="Contenido original.",
    )

    assert result == verified_draft
    fetch_full_draft_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-1",
    )


@patch("app.tools.external.gmail.draft_updates.update_gmail_draft")
def test_update_verification_rejects_a_different_draft_id(
    update_draft_mock: Mock,
) -> None:
    update_draft_mock.return_value = {"id": "different-draft"}

    with pytest.raises(AppError) as error_info:
        _update_and_verify_draft(
            access_token="access-token",
            draft={
                "draft_id": "draft-1",
                "to": "lina@example.com",
                "subject": "Factura",
                "body": "Contenido.",
            },
            recipient_email="lina@example.com",
            subject="Factura corregida",
            body="Contenido.",
        )

    assert error_info.value.code == "external_provider_invalid_response"
