from sqlalchemy.orm import Session

from app.integrations.gmail.search import build_gmail_query
from app.integrations.gmail.sent import (
    fetch_sent_gmail_messages,
    fetch_specific_sent_gmail_messages,
)
from app.services.external_auth_service import get_valid_google_access_token


def gmail_get_sent_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
) -> dict:
    max_results = min(max(int(arguments.get("max_results", 3)), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    result = fetch_sent_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )

    if result:
        return result

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
    return fetch_specific_sent_gmail_messages(
        access_token=access_token,
        query=query,
        max_results=arguments.get("max_results", 3),
    )
