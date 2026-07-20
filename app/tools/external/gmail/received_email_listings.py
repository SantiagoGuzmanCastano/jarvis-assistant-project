from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.integrations.gmail.messages import (
    fetch_latest_gmail_messages,
    fetch_specific_gmail_message_format_FSD,
    fetch_unread_gmail_messages,
)
from app.integrations.gmail.search import build_gmail_query
from app.services.external_auth_service import get_valid_google_access_token


def format_gmail_message_metadata(
    message_data: list[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(message_data, dict):
        raw_emails = message_data.get("emails", [])
        emails = raw_emails if isinstance(raw_emails, list) else []
    else:
        emails = message_data

    formatted_emails: list[dict[str, Any]] = []
    for message in emails:
        headers = message.get("payload", {}).get("headers", [])
        header_values = {
            header.get("name", "").lower(): header.get("value")
            for header in headers
        }
        date_value = header_values.get("date")
        internal_date = message.get("internalDate")

        if internal_date:
            date_value = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=ZoneInfo("UTC"),
            ).astimezone(ZoneInfo("America/Bogota")).isoformat()

        formatted_emails.append(
            {
                "sender": header_values.get("from", ""),
                "subject": header_values.get("subject", ""),
                "date": date_value or "",
                "snippet": message.get("snippet", ""),
            }
        )

    return formatted_emails


def get_unread_emails_tool(arguments: dict, user_id: int, session: Session) -> dict:
    query = build_gmail_query(
        search_scope="unread",
        start_date=arguments.get("start_date", ""),
        end_date=arguments.get("end_date", ""),
        search_keywords=arguments.get("search_keywords", []),
        sender_hint=arguments.get("sender_hint", []),
        recipient_hint=None,
    )
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_unread_gmail_messages(
        access_token=access_token,
        max_results=arguments.get("max_results", 3),
        query=query,
    )
    emails = format_gmail_message_metadata(message_list)
    return {
        "emails": emails,
        "returned_count": len(emails),
        "has_more": message_list.get("has_more", False),
        "next_page_token": message_list.get("next_page_token"),
    }


def get_latest_emails_tool(arguments: dict, user_id: int, session: Session) -> dict:
    max_results = min(max(int(arguments.get("max_results", 3)), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )
    return {
        "emails": format_gmail_message_metadata(message_list),
        "returned_count": message_list.get("returned_count", 0),
        "has_more": message_list.get("has_more", False),
        "next_page_token": message_list.get("next_page_token"),
    }


def gmail_search_email_message_tool(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    query = build_gmail_query(
        search_scope="received",
        start_date=arguments.get("start_date", ""),
        end_date=arguments.get("end_date", ""),
        search_keywords=arguments.get("search_keywords", []),
        sender_hint=arguments.get("sender_hint", []),
        recipient_hint=None,
    )
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    return fetch_specific_gmail_message_format_FSD(
        access_token=access_token,
        query=query,
        max_results=arguments.get("max_results", 3),
    )
