
from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import create_draft_reply
from app.integrations.gmail.messages import (
    fetch_specific_gmail_message_format_MORE,
    search_latest_gmail_messages_for_metadata,
)
from app.integrations.gmail.search import build_gmail_query
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import get_valid_google_access_token
from app.tools.external.gmail.helpers import extract_gmail_reply_context


def _save_active_reply_draft(
    *,
    created_draft: dict,
    recipient_email: str,
    subject: str,
    body: str,
    user_id: int,
    session: Session,
    conversation_id: int,
) -> None:
    create_tool_state(
        payload={
            "active_draft": {
                "draft_id": created_draft["id"],
                "to": recipient_email,
                "subject": subject,
                "body": body,
            },
        },
        user_id=user_id,
        session=session,
        conversation_id=conversation_id,
        state_type="gmail_active_draft",
    )


def gmail_create_reply_draft_tool(arguments: dict, user_id: int, session: Session, conversation_id: int):
    access_token = get_valid_google_access_token(user_id=user_id,session=session)
    reply_body = arguments.get("reply_body", "")
    recent_result_position = arguments.get("recent_result_position")

    selection_type = (
        "recent_email"
        if recent_result_position is not None
        else "specific_email"
    )

    if selection_type == "recent_email":
        if not reply_body:
            return {
                "success": False,
                "reason": "missing_body",
                "message": "Body is required for the new draft content, request it to the user",
            }

        recent_email_position = recent_result_position

        try:
            recent_email_position = int(recent_email_position)
        except (TypeError, ValueError):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent result position must be a positive integer.",
            }

        if recent_email_position < 1:
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "Recent result position must be at least 1.",
            }

        max_results = recent_email_position

        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

        emails_found = search_latest_gmail_messages_for_metadata(
                    access_token=access_token,
                    max_results=max_results)

        if recent_email_position < 1 or recent_email_position > len(emails_found):
            return {
                "success": False,
                "reason": "invalid_recent_result_position",
                "message": "The requested email position is out of range.",
                "available_emails": len(emails_found),
            }

        reply_context = extract_gmail_reply_context(emails=emails_found, email_index=recent_email_position - 1)

        created_draft = create_draft_reply(
                    access_token=access_token,
                    thread_id=reply_context["threadId"],
                    original_message_id=reply_context["original_message_id"],
                    references=reply_context["references"],
                    recipient_email=reply_context["recipient_email"],
                    subject=reply_context["subject"],
                    body=reply_body)

        _save_active_reply_draft(
            created_draft=created_draft,
            recipient_email=reply_context["recipient_email"],
            subject=reply_context["subject"],
            body=reply_body,
            user_id=user_id,
            session=session,
            conversation_id=conversation_id,
        )

        return {
            "success": True,
            "draft": {
                "draft_id": created_draft["id"],
                "message_id": created_draft["message"]["id"],
                "thread_id": created_draft["message"]["threadId"],
                "recipient_email": reply_context["recipient_email"],
                "subject": reply_context["subject"],
            },
        }

    if selection_type == "specific_email":

        selected_result_position = arguments.get("selected_result_position")
        print("\nSelected result position mode:")
        if selected_result_position is not None:
            try:
                selected_result_position = int(selected_result_position)
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "reason": "invalid_selected_result_position",
                    "message": "Selected email position must be a positive integer.",
                }

            tool_payload = get_tool_payload(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                state_type="gmail_create_reply_draft_selection",
            )

            if tool_payload is None:
                return {
                    "success": False,
                    "reason": "missing_tool_state",
                }

            if "emails_found" not in tool_payload:
                return {
                    "success": False,
                    "reason": "invalid_reply_selection_state",
                    "message": "No pending email selection was found for creating a reply draft.",
                }

            matches = tool_payload["emails_found"]

            if (
                not isinstance(matches, list)
                or selected_result_position < 1
                or selected_result_position > len(matches)
            ):
                return {
                    "success": False,
                    "reason": "invalid_selected_result_position",
                    "message": "Selected email position is out of range.",
                }

            reply_body = arguments.get("reply_body") or tool_payload.get("reply_body", "")

            if not reply_body:
                return {
                    "success": False,
                    "reason": "missing_body",
                    "message": "No reply content was found for the selected email.",
                }

            selected_match = matches[selected_result_position - 1]
            print("\nEmail selected:")
            print(selected_match)

            created_draft = create_draft_reply(
                    access_token=access_token,
                    thread_id=selected_match["thread_id"],
                    original_message_id=selected_match["original_message_id"],
                    references=selected_match["references"],
                    recipient_email=selected_match["recipient_email"],
                    subject=selected_match["subject"],
                    body=reply_body)
            delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)
            _save_active_reply_draft(
                created_draft=created_draft,
                recipient_email=selected_match["recipient_email"],
                subject=selected_match["subject"],
                body=reply_body,
                user_id=user_id,
                session=session,
                conversation_id=conversation_id,
            )
            print("\nDeleted tool state!")
            return {
                "success": True,
                "draft": {
                    "draft_id": created_draft["id"],
                    "message_id": created_draft["message"]["id"],
                    "thread_id": created_draft["message"]["threadId"],
                    "recipient_email": selected_match["recipient_email"],
                    "subject": selected_match["subject"],
                },
            }

        if not reply_body:
            return {
                "success": False,
                "reason": "missing_body",
                "message": "Body is required for the new draft content, request it to the user",
            }

        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )

        max_results = arguments.get("max_results", 3)
        start_date = arguments.get("start_date", "")
        end_date = arguments.get("end_date", "")
        search_keywords = arguments.get("search_keywords", [])
        sender_hint = arguments.get("sender_hint", [])

        query = build_gmail_query(search_scope="received",start_date=start_date, end_date=end_date, search_keywords=search_keywords, sender_hint=sender_hint)

        print("\nQuery:")
        print(query)
        email_results = fetch_specific_gmail_message_format_MORE(
            access_token=access_token,
            max_results=max_results,
            query=query,
        )
        emails_fetched = email_results["emails"]

        print("\nEMAILS FOUND")
        print(emails_fetched)


        if len(emails_fetched) == 0:
            return {
                "success": False,
                "reason": "no_matching_email",
                "message": "No matching email was found.",
                "matching_emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        if len(emails_fetched) == 1:
            created_draft = create_draft_reply(
                    access_token=access_token,
                    thread_id=emails_fetched[0]["thread_id"],
                    original_message_id=emails_fetched[0]["original_message_id"],
                    references=emails_fetched[0]["references"],
                    recipient_email=emails_fetched[0]["recipient_email"],
                    subject=emails_fetched[0]["subject"],
                    body=reply_body,)

            _save_active_reply_draft(
                created_draft=created_draft,
                recipient_email=emails_fetched[0]["recipient_email"],
                subject=emails_fetched[0]["subject"],
                body=reply_body,
                user_id=user_id,
                session=session,
                conversation_id=conversation_id,
            )

            return {
                "success": True,
                "draft": {
                    "draft_id": created_draft["id"],
                    "message_id": created_draft["message"]["id"],
                    "thread_id": created_draft["message"]["threadId"],
                    "recipient_email": emails_fetched[0]["recipient_email"],
                    "subject": emails_fetched[0]["subject"],
                },
            }

        if len(emails_fetched) >1:
            create_tool_state(
                payload={
                    "emails_found": emails_fetched,
                    "reply_body": reply_body,
                },
                user_id=user_id,
                session=session,
                conversation_id=conversation_id,
                state_type="gmail_create_reply_draft_selection",
            )

            return({
                "success": False,
                "reason": "multiple_matching_emails",
                "message": "Multiple matching emails found, please specify which email you want to reply to.",
                "matching_emails": emails_fetched,
                "returned_count": email_results["returned_count"],
                "has_more": email_results["has_more"],
            })
