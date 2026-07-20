import base64
from unittest.mock import Mock, patch

from app.tools.external.gmail.received_email_reading import gmail_read_latest_email_tool


def _gmail_email(message_id: str, subject: str, body: str) -> dict:
    return {
        "id": message_id,
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


@patch("app.tools.external.gmail.received_email_reading.fetch_full_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_reading.get_valid_google_access_token")
def test_recent_position_returns_the_requested_email(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
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
