from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import gmail_move_email_to_trash_tool


def _received_email(message_id: str, subject: str) -> dict:
    return {
        "message_id": message_id,
        "sender": "ana@example.com",
        "subject": subject,
        "date": "2026-01-15T10:00:00-05:00",
        "snippet": "Factura pendiente.",
    }


@patch("app.tools.external.gmail_tools.delete_tool_state")
@patch("app.tools.external.gmail_tools.move_gmail_message_to_trash")
@patch("app.tools.external.gmail_tools.get_tool_payload")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
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

    assert result["trashed"] is True
    assert result["emails"][0]["subject"] == "Factura febrero"
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
        arguments={"requested_email_count": 2},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["trashed"] is False
    assert result["reason"] == "multiple_email_trash_not_supported"
