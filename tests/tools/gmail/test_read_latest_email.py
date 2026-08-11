import base64
from unittest.mock import Mock, patch

from app.tools.external.gmail.received_email_reading import gmail_read_latest_email_tool
from app.tools.registry import TOOLS


def _gmail_email(message_id: str, subject: str, body: str) -> dict:
    return {
        "id": message_id,
        "threadId": f"thread-{message_id}",
        "snippet": body,
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "ana@example.com"},
                {"name": "Subject", "value": subject},
                {"name": "Date", "value": "Mon, 1 Jun 2026 10:00:00 -0500"},
            ],
            "body": {"data": base64.urlsafe_b64encode(body.encode()).decode()},
        },
    }


def test_read_latest_email_registry_requires_conversation_id() -> None:
    assert TOOLS["gmail_read_latest_email"]["requires_conversation_id"] is True


@patch("app.tools.external.gmail.received_email_reading.create_tool_state")
@patch("app.tools.external.gmail.received_email_reading.fetch_full_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_reading.get_valid_google_access_token")
def test_recent_position_returns_the_requested_email(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    fetch_latest_mock.return_value = [
        _gmail_email("email-1", "Factura enero", "Primer correo"),
        _gmail_email("email-2", "Factura febrero", "Segundo correo"),
    ]
    access_token_mock.return_value = "access-token"

    result = gmail_read_latest_email_tool(
        arguments={"recent_result_position": 2},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result == {
        "success": True,
        "emails": [
            {
                "sender": "ana@example.com",
                "subject": "Factura febrero",
                "date": "Mon, 1 Jun 2026 10:00:00 -0500",
                "snippet": "Segundo correo",
                "body": "Segundo correo",
            }
        ],
        "returned_count": 1,
        "has_more": False,
    }
    fetch_latest_mock.assert_called_once_with(
        access_token="access-token",
        max_results=2,
    )
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_email",
        payload={
            "active_email": {
                "message_id": "email-2",
                "thread_id": "thread-email-2",
                "source": "received",
            }
        },
    )


@patch("app.tools.external.gmail.received_email_reading.create_tool_state")
@patch("app.tools.external.gmail.received_email_reading.fetch_full_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_reading.get_valid_google_access_token", return_value="access-token")
def test_single_latest_email_is_saved_as_active(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    fetch_latest_mock.return_value = [
        _gmail_email("email-1", "Factura enero", "Primer correo"),
    ]

    result = gmail_read_latest_email_tool(
        arguments={"max_results": 1},
        session=session,
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["returned_count"] == 1
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_email",
        payload={
            "active_email": {
                "message_id": "email-1",
                "thread_id": "thread-email-1",
                "source": "received",
            }
        },
    )


@patch("app.tools.external.gmail.received_email_reading.create_tool_state")
@patch("app.tools.external.gmail.received_email_reading.fetch_full_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_reading.get_valid_google_access_token", return_value="access-token")
def test_two_latest_emails_do_not_create_an_active_email(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
    create_state_mock: Mock,
) -> None:
    fetch_latest_mock.return_value = [
        _gmail_email("email-1", "Factura enero", "Primer correo"),
        _gmail_email("email-2", "Factura febrero", "Segundo correo"),
    ]

    result = gmail_read_latest_email_tool(
        arguments={"max_results": 2},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is True
    assert result["returned_count"] == 2
    create_state_mock.assert_not_called()


@patch("app.tools.external.gmail.received_email_reading.create_tool_state")
@patch(
    "app.tools.external.gmail.received_email_reading.fetch_full_latest_gmail_messages",
    return_value=[],
)
@patch("app.tools.external.gmail.received_email_reading.get_valid_google_access_token", return_value="access-token")
def test_empty_latest_email_result_does_not_create_an_active_email(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
    create_state_mock: Mock,
) -> None:
    result = gmail_read_latest_email_tool(
        arguments={"max_results": 1},
        session=Mock(),
        user_id=7,
        conversation_id=11,
    )

    assert result["success"] is False
    assert result["returned_count"] == 0
    create_state_mock.assert_not_called()
