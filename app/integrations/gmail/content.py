import base64

from app.core.errors import AppError


def _decode_body_data(value: str) -> str:
    try:
        padded_value = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded_value).decode(
            "utf-8",
            errors="replace",
        )
    except (TypeError, ValueError) as error:
        raise AppError(
            code="external_provider_invalid_response",
            message="Gmail returned invalid message content.",
            status_code=502,
        ) from error


def _extract_plain_text(payload: dict) -> str | None:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data")
    if mime_type == "text/plain" and isinstance(body_data, str):
        return _decode_body_data(body_data)

    for part in payload.get("parts", []):
        if isinstance(part, dict):
            text = _extract_plain_text(part)
            if text:
                return text

    if isinstance(body_data, str):
        return _decode_body_data(body_data)

    return None


def format_full_gmail_message(message: dict) -> dict:
    payload = message.get("payload")
    if not isinstance(payload, dict):
        raise AppError(
            code="external_provider_invalid_response",
            message="Gmail returned an invalid message.",
            status_code=502,
        )

    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in payload.get("headers", [])
        if isinstance(header, dict)
    }
    body = _extract_plain_text(payload) or message.get("snippet", "")
    if not isinstance(body, str):
        body = ""

    return {
        "sender": headers.get("from", ""),
        "recipient": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "body": body,
    }
