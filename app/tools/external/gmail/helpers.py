from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def format_gmail_message_metadata(
    message_data: list[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, Any]]:
    emails = message_data.get("emails", []) if isinstance(message_data, dict) else message_data
    if not isinstance(emails, list):
        return []

    formatted_emails = []
    for message in emails:
        headers = message.get("payload", {}).get("headers", [])
        values = {
            header.get("name", "").lower(): header.get("value", "")
            for header in headers
        }
        date = values.get("date", "")
        if message.get("internalDate"):
            date = datetime.fromtimestamp(
                int(message["internalDate"]) / 1000,
                tz=ZoneInfo("UTC"),
            ).astimezone(ZoneInfo("America/Bogota")).isoformat()
        formatted_emails.append(
            {
                "sender": values.get("from", ""),
                "subject": values.get("subject", ""),
                "date": date,
                "snippet": message.get("snippet", ""),
            }
        )
    return formatted_emails


def extract_gmail_reply_context(emails: list[dict], email_index: int) -> dict:
    email = emails[email_index]
    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in email["payload"]["headers"]
    }
    recipient_email = headers.get("reply-to") or headers.get("from", "")
    subject = headers.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    original_message_id = headers.get("message-id", "")
    references = headers.get("references", "")
    if original_message_id:
        references = f"{references} {original_message_id}".strip()
    return {
        "threadId": email["threadId"],
        "recipient_email": recipient_email,
        "subject": subject,
        "original_message_id": original_message_id,
        "references": references,
    }
