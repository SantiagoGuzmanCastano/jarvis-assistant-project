import base64

from app.integrations.gmail.content import format_full_gmail_message


def _encoded(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def test_format_full_gmail_message_extracts_nested_plain_text() -> None:
    result = format_full_gmail_message(
        {
            "snippet": "Snippet",
            "payload": {
                "mimeType": "multipart/alternative",
                "headers": [
                    {"name": "From", "value": "ana@example.com"},
                    {"name": "To", "value": "lina@example.com"},
                    {"name": "Subject", "value": "Reunión Jarvis"},
                    {
                        "name": "Date",
                        "value": "Thu, 30 Jul 2026 09:00:00 -0500",
                    },
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": _encoded(
                                "Reunión mañana de 10 a 11."
                            )
                        },
                    }
                ],
            },
        }
    )

    assert result == {
        "sender": "ana@example.com",
        "recipient": "lina@example.com",
        "subject": "Reunión Jarvis",
        "date": "Thu, 30 Jul 2026 09:00:00 -0500",
        "body": "Reunión mañana de 10 a 11.",
    }
