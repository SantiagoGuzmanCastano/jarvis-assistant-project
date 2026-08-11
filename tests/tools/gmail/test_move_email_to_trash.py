from unittest.mock import Mock, patch

from app.tools.external.gmail.received_email_actions import gmail_move_email_to_trash_tool


def _received_email(message_id: str, subject: str) -> dict:
    return {
        "message_id": message_id,
        "sender": "ana@example.com",
        "subject": subject,
        "date": "2026-01-15T10:00:00-05:00",
        "snippet": "Factura pendiente.",
    }


def _gmail_metadata_email(message_id: str, subject: str) -> dict:
    return {
        "id": message_id,
        "threadId": f"thread-{message_id}",
        "snippet": "Factura pendiente.",
        "payload": {
            "headers": [
                {"name": "From", "value": "ana@example.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Thu, 15 Jan 2026 10:00:00 -0500"},
            ]
        },
    }


@patch("app.tools.external.gmail.received_email_actions.delete_tool_state")
@patch("app.tools.external.gmail.received_email_actions.move_gmail_message_to_trash")
@patch("app.tools.external.gmail.received_email_actions.fetch_metadata_FSD_gmail_message")
@patch("app.tools.external.gmail.received_email_actions.get_valid_google_access_token")
@patch("app.tools.external.gmail.received_email_actions.get_tool_payload")
def test_active_email_moves_exact_message_to_trash(
    get_payload_mock: Mock,
    access_token_mock: Mock,
    fetch_metadata_mock: Mock,
    move_to_trash_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    get_payload_mock.return_value = {
        "active_email": {
            "message_id": "message-1",
            "thread_id": "thread-message-1",
            "source": "received",
        }
    }
    access_token_mock.return_value = "access-token"
    fetch_metadata_mock.return_value = _gmail_metadata_email(
        "message-1",
        "Factura enero",
    )

    result = gmail_move_email_to_trash_tool(
        arguments={
            "selection_source": "active",
            "requested_result_count": 1,
        },
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "success": True,
        "email": {
            "sender": "ana@example.com",
            "subject": "Factura enero",
            "date": "Thu, 15 Jan 2026 10:00:00 -0500",
            "snippet": "Factura pendiente.",
        },
    }
    get_payload_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_email",
    )
    fetch_metadata_mock.assert_called_once_with(
        message_id="message-1",
        access_token="access-token",
    )
    move_to_trash_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-1",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


@patch("app.tools.external.gmail.received_email_actions.delete_tool_state")
@patch("app.tools.external.gmail.received_email_actions.move_gmail_message_to_trash")
@patch("app.tools.external.gmail.received_email_actions.fetch_metadata_FSD_gmail_message")
@patch("app.tools.external.gmail.received_email_actions.get_valid_google_access_token")
@patch(
    "app.tools.external.gmail.received_email_actions.get_tool_payload",
    return_value=None,
)
def test_active_email_without_state_does_not_move_anything(
    get_payload_mock: Mock,
    access_token_mock: Mock,
    fetch_metadata_mock: Mock,
    move_to_trash_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    result = gmail_move_email_to_trash_tool(
        arguments={
            "selection_source": "active",
            "requested_result_count": 1,
        },
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "missing_active_email"
    access_token_mock.assert_not_called()
    fetch_metadata_mock.assert_not_called()
    move_to_trash_mock.assert_not_called()
    delete_state_mock.assert_not_called()


@patch("app.tools.external.gmail.received_email_actions.move_gmail_message_to_trash")
@patch("app.tools.external.gmail.received_email_actions.get_valid_google_access_token")
@patch("app.tools.external.gmail.received_email_actions.get_tool_payload")
def test_invalid_active_email_state_does_not_move_anything(
    get_payload_mock: Mock,
    access_token_mock: Mock,
    move_to_trash_mock: Mock,
) -> None:
    get_payload_mock.return_value = {
        "active_email": {
            "message_id": "",
            "thread_id": "thread-1",
            "source": "received",
        }
    }

    result = gmail_move_email_to_trash_tool(
        arguments={
            "selection_source": "active",
            "requested_result_count": 1,
        },
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "invalid_active_email_state"
    access_token_mock.assert_not_called()
    move_to_trash_mock.assert_not_called()


@patch("app.tools.external.gmail.received_email_actions.delete_tool_state")
@patch("app.tools.external.gmail.received_email_actions.move_gmail_message_to_trash")
@patch("app.tools.external.gmail.received_email_actions.get_tool_payload")
@patch("app.tools.external.gmail.received_email_actions.get_valid_google_access_token")
def test_selected_position_moves_exactly_one_received_email_to_trash(
    access_token_mock: Mock,
    get_payload_mock: Mock,
    move_to_trash_mock: Mock,
    delete_state_mock: Mock,
) -> None:
    session = Mock()
    emails = [
        _received_email("message-1", "Factura enero"),
        _received_email("message-2", "Factura febrero"),
    ]
    access_token_mock.return_value = "access-token"
    get_payload_mock.return_value = {
        "state_type": "gmail_move_email_to_trash_selection",
        "emails": emails,
    }

    result = gmail_move_email_to_trash_tool(
        arguments={"selected_result_position": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["email"]["subject"] == "Factura febrero"
    move_to_trash_mock.assert_called_once_with(
        access_token="access-token",
        message_id="message-2",
    )
    delete_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
    )


def test_multiple_received_email_trash_request_is_rejected() -> None:
    result = gmail_move_email_to_trash_tool(
        arguments={"requested_result_count": 2},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["reason"] == "multiple_email_trash_not_supported"


@patch("app.tools.external.gmail.received_email_actions.fetch_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_actions.delete_tool_state")
@patch("app.tools.external.gmail.received_email_actions.get_valid_google_access_token")
def test_recent_result_position_uses_received_email_flow(
    access_token_mock: Mock,
    delete_state_mock: Mock,
    fetch_latest_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    fetch_latest_mock.return_value = {"emails": []}

    result = gmail_move_email_to_trash_tool(
        arguments={"recent_result_position": 1},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["reason"] == "invalid_recent_result_position"
    fetch_latest_mock.assert_called_once_with(
        access_token="access-token",
        max_results=1,
    )
    delete_state_mock.assert_called_once()
