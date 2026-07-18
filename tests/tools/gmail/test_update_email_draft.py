from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_update_email_draft_tool


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.update_gmail_draft")
@patch("app.tools.external.gmail_tools.get_tool_payload")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_active_draft_update_preserves_unspecified_fields(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    update_draft_mock: Mock,
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

    result = gmail_update_email_draft_tool(
        user_id=7,
        session=session,
        arguments={
            "selection_source": "active",
            "new_subject": "Factura enero corregida",
        },
        conversation_id=11,
    )

    assert result["updated"] is True
    assert result["selected_draft"]["to"] == "lina@example.com"
    assert result["selected_draft"]["subject"] == "Factura enero corregida"
    assert result["selected_draft"]["body"] == "Contenido original."
    update_draft_mock.assert_called_once_with(
        access_token="access-token",
        body="Contenido original.",
        subject="Factura enero corregida",
        recipient_email="lina@example.com",
        draft_id="draft-1",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )
    create_state_mock.assert_called_once()


@patch("app.tools.external.gmail_tools.create_tool_state")
@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.fetch_specific_gmail_drafts_full")
@patch("app.tools.external.gmail_tools.build_gmail_query", return_value="to:lina@example.com")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
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

    assert result["updated"] is False
    assert result["reason"] == "multiple_matching_drafts"
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        payload={
            "drafts": drafts,
            "new_recipient_email": "",
            "new_subject": "Factura corregida",
            "new_body": "",
        },
    )
