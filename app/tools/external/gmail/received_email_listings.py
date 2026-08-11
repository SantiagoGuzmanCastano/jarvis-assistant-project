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
from app.repositories.conversation import create_tool_state
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


def build_email_selection_candidates(
    message_data: list[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(message_data, dict):
        raw_emails = message_data.get("emails", [])
        emails = raw_emails if isinstance(raw_emails, list) else []
    else:
        emails = message_data

    metadata = format_gmail_message_metadata(emails)
    return [
        {
            "position": position,
            "message_id": email.get("id"),
            "thread_id": email.get("threadId"),
            **formatted_email,
        }
        for position, (email, formatted_email) in enumerate(
            zip(emails, metadata, strict=True),
            start=1,
        )
    ]


def public_email_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            key: candidate.get(key)
            for key in (
                "position",
                "sender",
                "subject",
                "date",
                "snippet",
            )
        }
        for candidate in candidates
    ]


def get_unread_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
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
    candidates = build_email_selection_candidates(message_list)
    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type="gmail_email_selection",
        payload={
            "emails": candidates,
            "search_arguments": {
                "start_date": arguments.get("start_date"),
                "end_date": arguments.get("end_date"),
                "sender_hint": arguments.get("sender_hint", []),
                "search_keywords": arguments.get(
                    "search_keywords",
                    [],
                ),
            },
        },
        session=session,
    )
    return {
        "emails": public_email_candidates(candidates),
        "returned_count": len(candidates),
        "has_more": message_list.get("has_more", False),
        "next_page_token": message_list.get("next_page_token"),
    }


def get_latest_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    max_results = min(max(int(arguments.get("max_results", 3)), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )
    candidates = build_email_selection_candidates(message_list)
    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type="gmail_email_selection",
        payload={
            "emails": candidates,
            "search_arguments": {
                "start_date": None,
                "end_date": None,
                "sender_hint": [],
                "search_keywords": [],
            },
        },
        session=session,
    )
    return {
        "emails": public_email_candidates(candidates),
        "returned_count": len(candidates),
        "has_more": message_list.get("has_more", False),
        "next_page_token": message_list.get("next_page_token"),
    }


def gmail_search_email_message_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
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
    search_result = fetch_specific_gmail_message_format_FSD(
        access_token=access_token,
        query=query,
        max_results=arguments.get("max_results", 3),
    )
    emails = search_result.get("emails", [])
    candidates = [
        {
            "position": position,
            "message_id": email.get("message_id"),
            "thread_id": email.get("thread_id"),
            "sender": email.get("sender", ""),
            "subject": email.get("subject", ""),
            "date": email.get("date", ""),
            "date_iso": email.get("date_iso", ""),
            "snippet": email.get("snippet", ""),
        }
        for position, email in enumerate(emails, start=1)
        if isinstance(email, dict)
    ]

    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type="gmail_email_selection",
        payload={
            "emails": candidates,
            "search_arguments": {
                "start_date": arguments.get("start_date"),
                "end_date": arguments.get("end_date"),
                "sender_hint": arguments.get("sender_hint", []),
                "search_keywords": arguments.get(
                    "search_keywords",
                    [],
                ),
            },
        },
        session=session,
    )

    return {
        **search_result,
        "emails": candidates,
        "returned_count": len(candidates),
    }
