from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import (
    fetch_gmail_drafts,
    fetch_specific_gmail_drafts,
    format_gmail_draft_candidate,
    send_gmail_draft,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import create_tool_state, delete_tool_state, get_tool_payload
from app.services.external_auth_service import get_valid_google_access_token


def gmail_send_drafted_email_tool(
    arguments: dict,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> dict:
    requested_result_count = arguments.get("requested_result_count", 1)
    if requested_result_count is None or int(requested_result_count) > 1:
        return {
            "success": False,
            "reason": "multiple_draft_send_not_supported",
            "message": "Only one draft can be sent per request.",
        }
    if not int(requested_result_count):
        return {
            "success": False,
            "reason": "incorrect_draft_send",
            "message": "A draft to send is required.",
        }

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    selected_result_position = arguments.get("selected_result_position")
    if selected_result_position is not None:
        selected_result_position = int(selected_result_position)
        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_draft_selection",
        )
        drafts = tool_payload.get("drafts") if isinstance(tool_payload, dict) else None
        if not isinstance(drafts, list):
            return {
                "success": False,
                "reason": "missing_tool_state",
                "message": "No previous draft selection was found.",
            }
        if not 1 <= selected_result_position <= len(drafts):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected draft position is out of range.",
            }

        selected_draft = drafts[selected_result_position - 1]
        send_gmail_draft(
            draft_id=selected_draft["draft_id"],
            access_token=access_token,
        )
        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
        return {"success": True, "draft": selected_draft}

    recent_result_position = arguments.get("recent_result_position")
    if recent_result_position is not None:
        recent_result_position = int(recent_result_position)
        if recent_result_position < 1:
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent draft position must be at least 1.",
            }

        recent_drafts = fetch_gmail_drafts(
            access_token=access_token,
            max_results=recent_result_position,
        )
        if recent_result_position > len(recent_drafts):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Requested recent draft position is out of range.",
            }

        selected_draft = recent_drafts[recent_result_position - 1]
        send_gmail_draft(draft_id=selected_draft["id"], access_token=access_token)
        return {
            "success": True,
            "draft": format_gmail_draft_candidate(
                draft=selected_draft,
                position=recent_result_position,
            ),
        }

    recipient_hint = arguments.get("recipient_hint", [])
    search_keywords = arguments.get("search_keywords", [])
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    if not recipient_hint and not search_keywords and not start_date and not end_date:
        return {
            "success": False,
            "reason": "missing_draft_search_fields",
            "message": "Missing information required to identify the draft.",
        }

    query = build_gmail_query(
        search_scope="draft",
        start_date=start_date,
        end_date=end_date,
        search_keywords=search_keywords,
        recipient_hint=recipient_hint,
    )
    draft_results = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=min(max(int(arguments.get("max_results", 5)), 1), 15),
        query=query,
    )
    drafts = draft_results["drafts"]
    if not drafts:
        return {
            "success": False,
            "reason": "no_matching_draft",
            "message": "No matching draft was found.",
        }
    if len(drafts) > 1:
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            state_type="gmail_draft_selection",
            payload={"drafts": drafts},
            session=session,
        )
        return {
            "success": False,
            "reason": "multiple_matching_drafts",
            "message": "Multiple matching drafts found. Select one to send.",
            "matching_drafts": drafts,
            "returned_count": draft_results["returned_count"],
            "has_more": draft_results["has_more"],
        }

    selected_draft = drafts[0]
    send_gmail_draft(draft_id=selected_draft["draft_id"], access_token=access_token)
    return {"success": True, "draft": selected_draft}
