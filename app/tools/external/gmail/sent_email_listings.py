from sqlalchemy.orm import Session

from app.integrations.gmail.search import build_gmail_query
from app.integrations.gmail.sent import (
    fetch_sent_gmail_messages,
    fetch_specific_sent_gmail_messages,
)
from app.repositories.conversation import create_tool_state
from app.services.external_auth_service import get_valid_google_access_token


def _sent_email_candidates(emails: list[dict]) -> list[dict]:
    return [
        {
            **email,
            "position": position,
        }
        for position, email in enumerate(emails, start=1)
        if isinstance(email, dict)
    ]


def _store_sent_email_selection(
    *,
    emails: list[dict],
    search_arguments: dict,
    user_id: int,
    conversation_id: int | None,
    session: Session,
) -> None:
    if conversation_id is None:
        return

    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type="gmail_sent_email_selection",
        payload={
            "emails": emails,
            "search_arguments": search_arguments,
        },
        session=session,
    )


def gmail_get_sent_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int | None = None,
) -> dict:
    max_results = min(max(int(arguments.get("max_results", 3)), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    result = fetch_sent_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )

    if result:
        emails = _sent_email_candidates(result.get("emails", []))
        _store_sent_email_selection(
            emails=emails,
            search_arguments={"max_results": max_results},
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
        return {
            **result,
            "emails": emails,
            "returned_count": len(emails),
        }

    return {
        "emails": [],
        "returned_count": 0,
        "has_more": False,
        "next_page_token": None,
    }


def gmail_search_sent_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int | None = None,
) -> dict:
    query = build_gmail_query(
        search_scope="sent",
        start_date=arguments.get("start_date", ""),
        end_date=arguments.get("end_date", ""),
        search_keywords=arguments.get("search_keywords", []),
        recipient_hint=arguments.get("recipient_hint", []),
        sender_hint=None,
    )
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    result = fetch_specific_sent_gmail_messages(
        access_token=access_token,
        query=query,
        max_results=arguments.get("max_results", 3),
        search_keywords=arguments.get("search_keywords", []),
    )
    emails = _sent_email_candidates(result.get("emails", []))
    _store_sent_email_selection(
        emails=emails,
        search_arguments={
            "start_date": arguments.get("start_date"),
            "end_date": arguments.get("end_date"),
            "recipient_hint": arguments.get("recipient_hint", []),
            "search_keywords": arguments.get("search_keywords", []),
        },
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
    return {
        **result,
        "emails": emails,
        "returned_count": len(emails),
    }
