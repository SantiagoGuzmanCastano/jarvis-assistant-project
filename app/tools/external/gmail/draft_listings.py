from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import (
    fetch_gmail_draft_full,
    fetch_specific_gmail_drafts,
    format_gmail_draft_full,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import create_tool_state
from app.services.external_auth_service import get_valid_google_access_token


def gmail_get_drafted_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    max_results = min(max(int(arguments.get("max_results", 3)), 1), 5)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    draft_results = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=max_results,
        query="",
    )

    drafts = draft_results.get("drafts", [])
    if len(drafts) == 1:
        active_draft = format_gmail_draft_full(
            draft=fetch_gmail_draft_full(
                access_token=access_token,
                draft_id=drafts[0]["draft_id"],
            ),
            position=drafts[0]["position"],
        )
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_active_draft",
            payload={"active_draft": active_draft},
        )

    return draft_results


def gmail_search_drafted_emails_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    max_results = min(max(int(arguments.get("max_results", 5)), 1), 15)
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    recipient_hint = arguments.get("recipient_hint", [])
    search_keywords = arguments.get("search_keywords", [])

    query = build_gmail_query(
        search_scope="draft",
        start_date=start_date,
        end_date=end_date,
        search_keywords=search_keywords,
        recipient_hint=recipient_hint,
    )
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    draft_results = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    drafts = draft_results.get("drafts", [])
    if len(drafts) == 1:
        active_draft = format_gmail_draft_full(
            draft=fetch_gmail_draft_full(
                access_token=access_token,
                draft_id=drafts[0]["draft_id"],
            ),
            position=drafts[0]["position"],
        )
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type="gmail_active_draft",
            payload={"active_draft": active_draft},
            session=session,
        )
    elif drafts:
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type="gmail_draft_selection",
            payload={"drafts": drafts},
            session=session,
        )

    return draft_results
