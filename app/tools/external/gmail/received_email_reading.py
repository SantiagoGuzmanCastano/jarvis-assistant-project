import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.integrations.gmail.messages import (
    fetch_full_latest_gmail_messages,
    fetch_full_specific_gmail_messages,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import create_tool_state, delete_tool_state, get_tool_payload
from app.services.external_auth_service import get_valid_google_access_token


def _format_full_email(email: dict) -> dict:
    payload = email.get("payload", {})
    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in payload.get("headers", [])
    }
    body_data = payload.get("body", {}).get("data")
    if body_data:
        body_data += "=" * (-len(body_data) % 4)
        body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
    else:
        body = email.get("snippet", "")

    return {
        "sender": headers.get("from", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "snippet": email.get("snippet", ""),
        "body": body,
    }


def gmail_read_latest_email_tool(user_id: int, session: Session, arguments: dict) -> dict:

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    recent_result_position = arguments.get("recent_result_position")

    if recent_result_position is not None:
        recent_result_position = int(recent_result_position)

        if recent_result_position < 1:
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }
        

        emails = fetch_full_latest_gmail_messages(
            access_token=access_token,
            max_results=recent_result_position,
        )


        if recent_result_position > len(emails):
            return {
                "success": False,
                "reason": "recent_result_position_out_of_range",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }
        return {
            "success": True,
            "emails": [_format_full_email(emails[recent_result_position - 1])],
            "returned_count": 1,
            "has_more": False,
        }

    max_results = min(max(int(arguments.get("max_results", 1)), 1), 2)
    emails = fetch_full_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )
    formatted_emails = [_format_full_email(email) for email in emails]
    return {
        "success": bool(formatted_emails),
        "emails": formatted_emails,
        "returned_count": len(formatted_emails),
        "has_more": False,
    }


def _format_candidates(emails: list[dict]) -> list[dict]:
    candidates = []
    for position, email in enumerate(emails, start=1):
        headers = {
            header.get("name", "").lower(): header.get("value", "")
            for header in email.get("payload", {}).get("headers", [])
        }
        date_value = headers.get("date", "")
        if email.get("internalDate"):
            date_value = datetime.fromtimestamp(
                int(email["internalDate"]) / 1000,
                tz=ZoneInfo("UTC"),
            ).astimezone(ZoneInfo("America/Bogota")).isoformat()
        return_value = {
            "position": position,
            "sender": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            "date": date_value,
            "snippet": email.get("snippet", ""),
        }
        candidates.append(return_value)
    return candidates


def gmail_read_specific_email_tool(arguments: dict,session: Session,user_id: int,conversation_id: int) -> dict:
    if arguments.get("requested_result_count", 1) > 1:
        return {"success": False, "reason": "multiple_email_read_not_supported", "message": "Only one complete email can be read per request. Ask the user which email they want to read first.", "emails": [], "returned_count": 0, "has_more": False}

    selected_position = arguments.get("selected_result_position")
    if selected_position is not None:

        payload = get_tool_payload(user_id=user_id, conversation_id=conversation_id, session=session, state_type="gmail_read_specific_email_selection")
        emails = payload.get("emails") if isinstance(payload, dict) else None

        if not isinstance(emails, list):
            return {"success": False,
                    "reason": "missing_tool_state",
                    "message": "No previous email selection was found.",
                    "emails": [],
                    "returned_count": 0,
                    "has_more": False}
        
        selected_position = int(selected_position)

        if not 1 <= selected_position <= len(emails):
            return {"success": False,
            "reason": "invalid_selected_result_position",
            "message": "Selected email position is out of range.",
            "emails": [],
            "returned_count": 0,
            "has_more": False}
        
        delete_tool_state(user_id=user_id, conversation_id=conversation_id, session=session)
        return {"success": True, "emails": [_format_full_email(emails[selected_position - 1])], "returned_count": 1, "has_more": False}

    query = build_gmail_query(search_scope="received",
        start_date=arguments.get("start_date", ""),
        end_date=arguments.get("end_date", ""),
        search_keywords=arguments.get("search_keywords", []),
        sender_hint=arguments.get("sender_hint", []))

    emails = fetch_full_specific_gmail_messages(access_token=get_valid_google_access_token(user_id=user_id, session=session), max_results=arguments.get("max_results", 3), query=query)
    
    if not emails:
        return {"success": False,
        "reason": "email_not_found",
        "message": "No email matched the provided query.",
        "emails": [], "returned_count": 0,
        "has_more": False}


    if len(emails) == 1:
        return {"success": True,
        "emails": [_format_full_email(emails[0])],
        "returned_count": 1,
        "has_more": False}
    
    candidates = _format_candidates(emails)
    create_tool_state(user_id=user_id, conversation_id=conversation_id, session=session, payload={"emails": emails}, state_type="gmail_read_specific_email_selection")

    return {
        "success": False,
        "reason": "multiple_matching_emails",
        "message": "Multiple emails matched the query. Please specify which one you want to read.",
        "matching_emails": candidates,
        "returned_count": len(candidates),
        "has_more": False
    }
