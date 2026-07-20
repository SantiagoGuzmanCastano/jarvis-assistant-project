from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import (
    fetch_gmail_draft_full,
    fetch_gmail_drafts,
    fetch_specific_gmail_drafts_full,
    format_gmail_draft_full,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import get_valid_google_access_token


def gmail_read_specific_draft_tool(arguments: dict, session: Session, user_id: int, conversation_id: int,
):
    requested_result_count = arguments.get("requested_result_count", 1)
    selected_result_position = arguments.get("selected_result_position")
    recent_result_position = arguments.get("recent_result_position")
    reuse_previous_search = arguments.get("reuse_previous_search", False)

    try:
        requested_result_count = int(requested_result_count)
    except (TypeError, ValueError):
        return {
            "success": False,
            "reason": "invalid_requested_result_count",
            "message": "Requested result count must be a valid number.",
            "drafts": [],
            "returned_count": 0,
            "has_more": False,
        }

    if requested_result_count != 1:
        return {
            "success": False,
            "reason": "multiple_draft_read_not_supported",
            "message": "Only one complete draft can be read per request.",
            "drafts": [],
            "returned_count": 0,
            "has_more": False,
        }

    if recent_result_position is not None:
        try:
            recent_result_position = int(recent_result_position)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent draft position must be a valid number.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        if recent_result_position < 1:
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent draft position must be at least 1.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
        access_token = get_valid_google_access_token(user_id=user_id, session=session)
        recent_drafts = fetch_gmail_drafts(
            access_token=access_token,
            max_results=recent_result_position,
        )

        if recent_result_position > len(recent_drafts):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Requested recent draft position is out of range.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        selected_draft = format_gmail_draft_full(
            draft=fetch_gmail_draft_full(
                draft_id=recent_drafts[recent_result_position - 1]["id"],
                access_token=access_token,
            ),
            position=recent_result_position,
        )

        return {
            "success": True,
            "drafts": [selected_draft],
            "returned_count": 1,
            "has_more": False,
        }

    if selected_result_position is not None:
        try:
            selected_result_position = int(selected_result_position)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected draft position must be a valid number.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_read_specific_draft_selection",
        )

        if (
            not isinstance(tool_payload, dict)
            or not isinstance(tool_payload.get("drafts"), list)
        ):
            return {
                "success": False,
                "reason": "missing_tool_state",
                "message": "No previous draft selection was found.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        drafts_to_choose = tool_payload["drafts"]

        if (
            selected_result_position < 1
            or selected_result_position > len(drafts_to_choose)
        ):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected draft position is out of range.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        selected_draft = drafts_to_choose[selected_result_position - 1]
        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

        return {
            "success": True,
            "drafts": [selected_draft],
            "returned_count": 1,
            "has_more": False,
        }

    if reuse_previous_search:
        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_read_specific_draft_selection",
        )

        search_arguments = (
            tool_payload.get("search_arguments")
            if isinstance(tool_payload, dict)
            else None
        )

        if not isinstance(search_arguments, dict):
            return {
                "success": False,
                "reason": "missing_previous_draft_search",
                "message": "No previous draft search is available to expand.",
                "drafts": [],
                "returned_count": 0,
                "has_more": False,
            }

        max_results = 15
        start_date = search_arguments.get("start_date")
        end_date = search_arguments.get("end_date")
        recipient_hint = search_arguments.get("recipient_hint", [])
        search_keywords = search_arguments.get("search_keywords", [])
    else:
        max_results = min(max(int(arguments.get("max_results", 5)), 1), 15)
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        recipient_hint = arguments.get("recipient_hint", [])
        search_keywords = arguments.get("search_keywords", [])

    if not recipient_hint and not search_keywords and not start_date and not end_date:
        return {
            "success": False,
            "reason": "missing_draft_search_fields",
            "message": "Missing information required to identify the draft.",
            "drafts": [],
            "returned_count": 0,
            "has_more": False,
        }

    query = build_gmail_query(
        search_scope="draft",
        start_date=start_date,
        end_date=end_date,
        search_keywords=search_keywords,
        recipient_hint=recipient_hint,
    )

    print('\nQuery:')
    print(query)

    delete_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    draft_results = fetch_specific_gmail_drafts_full(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )
    drafts_found = draft_results["drafts"]

    if not drafts_found:
        return {
            "success": False,
            "reason": "draft_not_found",
            "message": "No draft matched the provided query.",
            "drafts": [],
            "returned_count": 0,
            "has_more": False,
        }

    if len(drafts_found) == 1:
        return {
            "success": True,
            "drafts": [drafts_found[0]],
            "returned_count": 1,
            "has_more": False,
        }

    matching_drafts = [
        {
            "position": draft["position"],
            "draft_id": draft["draft_id"],
            "to": draft["to"],
            "subject": draft["subject"],
            "date": draft["date"],
            "snippet": draft["snippet"],
        }
        for draft in drafts_found
    ]

    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        state_type="gmail_read_specific_draft_selection",
        payload={
            "drafts": drafts_found,
            "search_arguments": {
                "start_date": start_date,
                "end_date": end_date,
                "recipient_hint": recipient_hint,
                "search_keywords": search_keywords,
            },
        },
        session=session,
    )

    return {
        "success": False,
        "reason": "multiple_matching_drafts",
        "message": "Multiple drafts matched the query. Please specify which one you want to read.",
        "matching_drafts": matching_drafts,
        "returned_count": draft_results["returned_count"],
        "has_more": draft_results["has_more"],
    }
