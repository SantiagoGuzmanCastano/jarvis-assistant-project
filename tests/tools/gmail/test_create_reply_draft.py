from unittest.mock import ANY, Mock, patch

from app.tools.external.gmail.reply_drafts import gmail_create_reply_draft_tool


def _replyable_email() -> dict:
    return {
        "threadId": "thread-1",
        "payload": {
            "headers": [
                {"name": "From", "value": "ana@example.com"},
                {"name": "Subject", "value": "Factura"},
                {"name": "Message-ID", "value": "<message-1@example.com>"},
            ]
        },
    }


@patch("app.tools.external.gmail.reply_drafts.create_draft_reply")
@patch("app.tools.external.gmail.reply_drafts.create_tool_state")
@patch("app.tools.external.gmail.reply_drafts.fetch_metadata_MORE_gmail_message")
@patch("app.tools.external.gmail.reply_drafts.get_tool_payload")
@patch("app.tools.external.gmail.reply_drafts.get_valid_google_access_token")
def test_active_email_creates_reply_draft_for_exact_message(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    fetch_email_mock: Mock,
    create_state_mock: Mock,
    create_reply_mock: Mock,
) -> None:
    session = Mock()
    get_payload_mock.return_value = {
        "active_email": {
            "message_id": "email-1",
            "thread_id": "thread-1",
            "source": "received",
        }
    }
    fetch_email_mock.return_value = _replyable_email()
    create_reply_mock.return_value = {
        "id": "draft-1",
        "message": {"id": "message-2", "threadId": "thread-1"},
    }
    access_token_mock.return_value = "access-token"

    result = gmail_create_reply_draft_tool(
        arguments={
            "selection_source": "active",
            "reply_body": "Gracias por la información.",
        },
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result == {
        "success": True,
        "draft": {
            "draft_id": "draft-1",
            "message_id": "message-2",
            "thread_id": "thread-1",
            "recipient_email": "ana@example.com",
            "subject": "Re: Factura",
        },
    }
    get_payload_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_email",
    )
    fetch_email_mock.assert_called_once_with(
        access_token="access-token",
        message_id="email-1",
    )
    create_reply_mock.assert_called_once_with(
        access_token="access-token",
        thread_id="thread-1",
        original_message_id="<message-1@example.com>",
        references="<message-1@example.com>",
        recipient_email="ana@example.com",
        subject="Re: Factura",
        body="Gracias por la información.",
    )
    create_state_mock.assert_called_once_with(
        payload={
            "active_draft": {
                "draft_id": "draft-1",
                "to": "ana@example.com",
                "subject": "Re: Factura",
                "body": "Gracias por la información.",
            },
        },
        user_id=7,
        session=session,
        conversation_id=11,
        state_type="gmail_active_draft",
    )


@patch("app.tools.external.gmail.reply_drafts.fetch_metadata_MORE_gmail_message")
@patch("app.tools.external.gmail.reply_drafts.get_tool_payload", return_value=None)
@patch("app.tools.external.gmail.reply_drafts.get_valid_google_access_token", return_value="access-token")
def test_active_email_without_state_returns_error(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    fetch_email_mock: Mock,
) -> None:
    result = gmail_create_reply_draft_tool(
        arguments={
            "selection_source": "active",
            "reply_body": "Gracias por la información.",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result == {
        "success": False,
        "reason": "missing_active_email",
        "message": "No active received email was found.",
    }
    fetch_email_mock.assert_not_called()


@patch("app.tools.external.gmail.reply_drafts.get_tool_payload")
@patch("app.tools.external.gmail.reply_drafts.get_valid_google_access_token", return_value="access-token")
def test_active_email_without_reply_body_preserves_state(
    access_token_mock: Mock,
    get_payload_mock: Mock,
) -> None:
    result = gmail_create_reply_draft_tool(
        arguments={
            "selection_source": "active",
            "reply_body": None,
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "missing_body"
    get_payload_mock.assert_not_called()


@patch("app.tools.external.gmail.reply_drafts.search_latest_gmail_messages_for_metadata")
@patch("app.tools.external.gmail.reply_drafts.delete_tool_state")
@patch("app.tools.external.gmail.reply_drafts.get_valid_google_access_token")
def test_recent_result_position_uses_recent_reply_flow(
    access_token_mock: Mock,
    delete_state_mock: Mock,
    search_latest_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    search_latest_mock.return_value = []

    result = gmail_create_reply_draft_tool(
        arguments={
            "recent_result_position": 1,
            "reply_body": "Gracias por la información.",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "invalid_recent_result_position"
    search_latest_mock.assert_called_once_with(
        access_token="access-token",
        max_results=1,
    )
    delete_state_mock.assert_called_once()


@patch("app.tools.external.gmail.reply_drafts.create_draft_reply")
@patch("app.tools.external.gmail.reply_drafts.create_tool_state")
@patch("app.tools.external.gmail.reply_drafts.search_latest_gmail_messages_for_metadata")
@patch("app.tools.external.gmail.reply_drafts.delete_tool_state")
@patch("app.tools.external.gmail.reply_drafts.get_valid_google_access_token")
def test_recent_reply_returns_normalized_draft_result(
    access_token_mock: Mock,
    delete_state_mock: Mock,
    search_latest_mock: Mock,
    create_state_mock: Mock,
    create_reply_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    search_latest_mock.return_value = [_replyable_email()]
    create_reply_mock.return_value = {
        "id": "draft-1",
        "message": {"id": "message-2", "threadId": "thread-1"},
    }

    result = gmail_create_reply_draft_tool(
        arguments={
            "recent_result_position": 1,
            "reply_body": "Gracias por la información.",
        },
        user_id=7,
        session=Mock(),
        conversation_id=11,
    )

    assert result == {
        "success": True,
        "draft": {
            "draft_id": "draft-1",
            "message_id": "message-2",
            "thread_id": "thread-1",
            "recipient_email": "ana@example.com",
            "subject": "Re: Factura",
        },
    }
    delete_state_mock.assert_called_once()
    create_state_mock.assert_called_once_with(
        payload={
            "active_draft": {
                "draft_id": "draft-1",
                "to": "ana@example.com",
                "subject": "Re: Factura",
                "body": "Gracias por la información.",
            },
        },
        user_id=7,
        session=ANY,
        conversation_id=11,
        state_type="gmail_active_draft",
    )
