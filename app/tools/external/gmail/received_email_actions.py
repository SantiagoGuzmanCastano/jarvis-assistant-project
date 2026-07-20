from sqlalchemy.orm import Session

from app.integrations.gmail.messages import (
    fetch_latest_gmail_messages,
    fetch_specific_gmail_message_format_FSD,
    move_gmail_message_to_trash,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import get_valid_google_access_token
from app.tools.external.gmail.helpers import format_gmail_message_metadata

def gmail_move_email_to_trash_tool(
    arguments: dict,
    session: Session,
    user_id: int,
    conversation_id: int,
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
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    if requested_result_count != 1:
        return {
            "success": False,
            "reason": "multiple_email_trash_not_supported",
            "message": "Only one email can be moved to trash per request.",
            "requested_result_count": requested_result_count,
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    access_token = get_valid_google_access_token(user_id=user_id, session=session)

    if recent_result_position is not None:
        try:
            recent_result_position = int(recent_result_position)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent result position must be a valid number.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        if recent_result_position < 1:
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent result position must be at least 1.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
        recent_email_results = fetch_latest_gmail_messages(
            access_token=access_token,
            max_results=recent_result_position,
        )
        recent_emails = recent_email_results["emails"]

        if recent_result_position > len(recent_emails):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Requested recent result position is out of range.",
                "available_emails": len(recent_emails),
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        selected_email = recent_emails[recent_result_position - 1]
        move_gmail_message_to_trash(
            access_token=access_token,
            message_id=selected_email["id"],
        )
        formatted_email = format_gmail_message_metadata([selected_email])[0]

        return {
            "success": True,
            "email": {
                "sender": formatted_email["from"],
                "subject": formatted_email["subject"],
                "date": formatted_email["date"],
                "snippet": formatted_email["snippet"],
            },
        }

    if selected_result_position is not None:
        try:
            selected_result_position = int(selected_result_position)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected email position must be a valid number.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_move_email_to_trash_selection",
        )

        if (
            not isinstance(tool_payload, dict)
            or not isinstance(tool_payload.get("emails"), list)
        ):
            return {
                "success": False,
                "reason": "missing_tool_state",
                "message": "No previous email selection was found.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        emails_to_choose = tool_payload["emails"]

        if (
            selected_result_position < 1
            or selected_result_position > len(emails_to_choose)
        ):
            return {
                "success": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected email position is out of range.",
                "available_positions": len(emails_to_choose),
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        selected_email = emails_to_choose[selected_result_position - 1]
        move_gmail_message_to_trash(
            access_token=access_token,
            message_id=selected_email["message_id"],
        )
        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

        return {
            "success": True,
            "email": {
                "sender": selected_email["sender"],
                "subject": selected_email["subject"],
                "date": selected_email["date"],
                "snippet": selected_email["snippet"],
            },
        }

    if reuse_previous_search:
        tool_payload = get_tool_payload(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_move_email_to_trash_selection",
        )
        search_arguments = (
            tool_payload.get("search_arguments")
            if isinstance(tool_payload, dict)
            else None
        )

        if not isinstance(search_arguments, dict):
            return {
                "success": False,
                "reason": "missing_previous_email_search",
                "message": "No previous email search is available to expand.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        max_results = 15
        start_date = search_arguments.get("start_date")
        end_date = search_arguments.get("end_date")
        sender_hint = search_arguments.get("sender_hint", [])
        search_keywords = search_arguments.get("search_keywords", [])
    else:
        try:
            max_results = min(max(int(arguments.get("max_results", 5)), 1), 15)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_max_results",
                "message": "max_results must be a valid number.",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        sender_hint = arguments.get("sender_hint", [])
        search_keywords = arguments.get("search_keywords", [])

    if not sender_hint and not search_keywords and not start_date and not end_date:
        return {
            "success": False,
            "reason": "missing_email_search_fields",
            "message": "Missing information required to identify the email.",
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    query = build_gmail_query(
        search_scope="received",
        start_date=start_date,
        end_date=end_date,
        search_keywords=search_keywords,
        sender_hint=sender_hint,
    )
    delete_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
    )
    email_results = fetch_specific_gmail_message_format_FSD(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )
    emails_found = email_results["emails"]

    if not emails_found:
        return {
            "success": False,
            "reason": "email_not_found",
            "message": "No email matched the provided query.",
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    if len(emails_found) == 1:
        selected_email = emails_found[0]
        move_gmail_message_to_trash(
            access_token=access_token,
            message_id=selected_email["message_id"],
        )

        return {
            "success": True,
            "email": {
                "sender": selected_email["sender"],
                "subject": selected_email["subject"],
                "date": selected_email["date"],
                "snippet": selected_email["snippet"],
            },
        }

    matching_emails = [
        {
            "position": position,
            "from": email["sender"],
            "subject": email["subject"],
            "date": email["date"],
            "snippet": email["snippet"],
        }
        for position, email in enumerate(emails_found, start=1)
    ]

    create_tool_state(
        user_id=user_id,
        conversation_id=conversation_id,
        session=session,
        state_type="gmail_move_email_to_trash_selection",
        payload={
            "emails": emails_found,
            "search_arguments": {
                "start_date": start_date,
                "end_date": end_date,
                "sender_hint": sender_hint,
                "search_keywords": search_keywords,
            },
        },
    )

    return {
        "success": False,
        "reason": "multiple_matching_emails",
        "message": "Multiple emails matched the query. Please specify which one to move to trash.",
        "matching_emails": matching_emails,
        "returned_count": email_results["returned_count"],
        "has_more": email_results["has_more"],
    }
