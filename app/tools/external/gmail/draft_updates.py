from datetime import date

from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import (
    fetch_gmail_draft_full,
    fetch_gmail_drafts,
    fetch_specific_gmail_drafts_full,
    format_gmail_draft_full,
    update_gmail_draft,
)
from app.integrations.gmail.search import build_gmail_query
from app.core.errors import AppError
from app.repositories.conversation import (
    create_tool_state,
    delete_tool_state,
    get_tool_payload,
)
from app.services.external_auth_service import get_valid_google_access_token


def _update_and_verify_draft(
    *,
    access_token: str,
    draft: dict,
    recipient_email: str,
    subject: str,
    body: str,
) -> dict:
    draft_id = draft["draft_id"]
    update_response = update_gmail_draft(
        access_token=access_token,
        body=body,
        subject=subject,
        recipient_email=recipient_email,
        draft_id=draft_id,
    )

    if not isinstance(update_response, dict) or update_response.get("id") != draft_id:
        raise AppError(
            code="external_provider_invalid_response",
            message="Gmail did not confirm the draft update.",
            status_code=502,
        )

    verified_draft = format_gmail_draft_full(
        draft=fetch_gmail_draft_full(
            access_token=access_token,
            draft_id=draft_id,
        ),
        position=draft.get("position", 1),
    )

    if (
        verified_draft["draft_id"] != draft_id
        or verified_draft["to"] != recipient_email
        or verified_draft["subject"] != subject
        or verified_draft["body"].strip() != body.strip()
    ):
        raise AppError(
            code="external_provider_invalid_response",
            message="Gmail did not confirm the draft update.",
            status_code=502,
        )

    return verified_draft

def gmail_update_email_draft_tool(user_id: int, session: Session, arguments: dict, conversation_id: int):

    access_token = get_valid_google_access_token(user_id=user_id,session=session,)
    recent_result_position = arguments.get("recent_result_position")
    selection_source = arguments.get("selection_source")

    if selection_source not in {"active", "recent", "search"}:
        return {
            "success": False,
            "reason": "invalid_selection_source",
            "message": "A valid draft selection source is required.",
        }

    if selection_source == "active":
        tool_payload = get_tool_payload(
            user_id=user_id,
            session=session,
            conversation_id=conversation_id,
            state_type="gmail_active_draft",
        )

        if tool_payload is None or "active_draft" not in tool_payload:
            return {
                "success": False,
                "reason": "missing_active_draft",
                "message": "No recently updated draft is available.",
            }

        selected_draft = tool_payload["active_draft"]

        print("\nDraft Seleccionado: ")
        print(selected_draft)
        
        requested_new_recipient_email = arguments.get("new_recipient_email", "")
        requested_new_subject = arguments.get("new_subject", "")
        requested_new_body = arguments.get("new_body", "")
                
        if (not requested_new_recipient_email and not requested_new_subject and not requested_new_body
            ):
            return {
                "success": False,
                "reason": "missing_update_fields",
                "message": (
                    "No update fields were provided. Please specify at least one field "
                    "to update: recipient, subject, or body."
                ),
                "missing_fields": [
                    "new_recipient_email",
                    "new_subject",
                    "new_body",
                ],
            }

        new_recipient_email = requested_new_recipient_email or selected_draft["to"]
        new_subject = requested_new_subject or selected_draft["subject"]
        new_body = requested_new_body or selected_draft["body"]

        updated_draft = _update_and_verify_draft(
            access_token=access_token,
            draft=selected_draft,
            body=new_body,
            subject=new_subject,
            recipient_email=new_recipient_email,
        )

        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            state_type="gmail_active_draft",
            payload={"active_draft": updated_draft},
        )

        return {
            "success": True,
            "new_recipient_email": new_recipient_email,
            "new_subject": new_subject,
            "new_body": new_body,
            "draft": updated_draft,
            "updated_fields": {
                "recipient_email": bool(requested_new_recipient_email),
                "subject": bool(requested_new_subject),
                "body": bool(requested_new_body),
            },
        }

    if selection_source == "recent":

        recent_result_position = arguments.get("recent_result_position")

        if recent_result_position is None:
            return {
                "success": False,
                "reason": "missing_recent_result_position",
                "message": "Missing recent draft position."
            }

        if recent_result_position is not None:
            try:
                recent_draft_position = int(recent_result_position)
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "reason": "invalid_recent_result_position",
                    "message": "Recent draft position must be a positive integer.",
                }

            if recent_draft_position < 1:
                return {
                    "success": False,
                    "reason": "invalid_recent_result_position",
                    "message": "Recent draft position must be a positive integer.",
                }

            recent_draft_index = recent_draft_position - 1

            max_results = max(recent_draft_position, 1)

            last_drafted_emails = fetch_gmail_drafts(
                access_token=access_token,
                max_results=max_results,
            )
            # la posición que pidio el usuario existe en esta lista?
            # recent_draft_index interno:
            # 0 = ultimo borrador
            # 1 = penultimo borrador
            if recent_draft_index < 0 or recent_draft_index >= len(last_drafted_emails):
                return {
                    "success": False,
                    "reason": "invalid_recent_result_position",
                    "message": "Requested recent draft position is out of range.",
                    "available_drafts": last_drafted_emails,
                }

            selected_draft_metadata = last_drafted_emails[recent_draft_index]
            selected_draft_full = fetch_gmail_draft_full(
                access_token=access_token,
                draft_id=selected_draft_metadata["id"],
            )
            selected_draft = format_gmail_draft_full(
                draft=selected_draft_full,
                position=recent_draft_position,
            )

            requested_new_recipient_email = arguments.get("new_recipient_email", "")
            requested_new_subject = arguments.get("new_subject", "")
            requested_new_body = arguments.get("new_body", "")

            if (
                not requested_new_recipient_email
                and not requested_new_subject
                and not requested_new_body
            ):
                return {
                    "success": False,
                    "reason": "missing_update_fields",
                    "message": (
                        "No update fields were provided. Please specify at least one field "
                        "to update: recipient, subject, or body."
                    ),
                    "missing_fields": [
                        "new_recipient_email",
                        "new_subject",
                        "new_body",
                    ],
                }

            new_recipient_email = requested_new_recipient_email or selected_draft["to"]
            new_subject = requested_new_subject or selected_draft["subject"]
            new_body = requested_new_body or selected_draft["body"]

            updated_draft = _update_and_verify_draft(
                access_token=access_token,
                draft=selected_draft,
                body=new_body,
                subject=new_subject,
                recipient_email=new_recipient_email,
            )

            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                state_type="gmail_active_draft",
                payload={"active_draft": updated_draft},
            )

            return {
                "success": True,
                "new_recipient_email": new_recipient_email,
                "new_subject": new_subject,
                "new_body": new_body,
                "draft": updated_draft,
                "updated_fields": {
                    "recipient_email": bool(requested_new_recipient_email),
                    "subject": bool(requested_new_subject),
                    "body": bool(requested_new_body),
                },
            }

    if selection_source == "search":

        selected_result_position = arguments.get("selected_result_position")

        if selected_result_position is not None:
            try:
                selected_result_position = int(selected_result_position)
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "reason": "invalid_selected_result_position",
                    "message": "Selected draft position must be a positive integer.",
                }

            tool_payload = get_tool_payload(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                state_type="gmail_draft_selection",
            )

            if tool_payload is None:
                tool_payload = get_tool_payload(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session=session,
                    state_type="gmail_update_draft_selection",
                )

            if tool_payload is None:
                return {
                    "success": False,
                    "reason": "missing_tool_state",
                    "message": "No previous draft selection was found."
                }

            if "drafts" not in tool_payload:
                return {
                    "success": False,
                    "reason": "invalid_tool_state",
                    "message": "Previous draft selection is invalid.",
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
                    "available_drafts": drafts_to_choose,
                }

            selected_draft = drafts_to_choose[selected_result_position - 1]

            if "body" not in selected_draft:
                selected_draft = format_gmail_draft_full(
                    draft=fetch_gmail_draft_full(
                        access_token=access_token,
                        draft_id=selected_draft["draft_id"],
                    ),
                    position=selected_draft["position"],
                )

            requested_new_recipient_email = (
                arguments.get("new_recipient_email")
                or tool_payload.get("new_recipient_email", "")
            )
            requested_new_subject = (
                arguments.get("new_subject")
                or tool_payload.get("new_subject", "")
            )
            requested_new_body = (
                arguments.get("new_body")
                or tool_payload.get("new_body", "")
            )

            if (
                not requested_new_recipient_email
                and not requested_new_subject
                and not requested_new_body
            ):
                return {
                    "success": False,
                    "reason": "missing_update_fields",
                    "message": (
                        "No update fields were provided. Please specify at least one field "
                        "to update: recipient, subject, or body."
                    ),
                    "missing_fields": [
                        "new_recipient_email",
                        "new_subject",
                        "new_body",
                    ],
                }

            new_recipient_email = requested_new_recipient_email or selected_draft["to"]
            new_subject = requested_new_subject or selected_draft["subject"]
            new_body = requested_new_body or selected_draft["body"]

            updated_draft = _update_and_verify_draft(
                access_token=access_token,
                draft=selected_draft,
                body=new_body,
                subject=new_subject,
                recipient_email=new_recipient_email,
            )

            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                state_type="gmail_active_draft",
                payload={"active_draft": updated_draft},
            )

            return {
                "success": True,
                "new_subject": new_subject,
                "new_body": new_body,
                "new_recipient_email": new_recipient_email,
                "draft": updated_draft,
                "updated_fields": {
                    "recipient_email": bool(requested_new_recipient_email),
                    "subject": bool(requested_new_subject),
                    "body": bool(requested_new_body),
                },
            }

        if selected_result_position is None:
            try:
                max_results = min(max(int(arguments.get("max_results", 5)), 1), 15)
            except (TypeError, ValueError):
                return {
                    "success": False,
                    "reason": "invalid_max_results",
                    "message": "max_results must be an integer between 1 and 15.",
                }

            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            recipient_hint = arguments.get("recipient_hint", [])
            search_keywords = arguments.get("search_keywords", [])

            if bool(start_date) != bool(end_date):
                return {
                    "success": False,
                    "reason": "incomplete_date_range",
                    "message": "start_date and end_date must be provided together.",
                }

            if start_date and end_date:
                try:
                    start = date.fromisoformat(start_date)
                    end = date.fromisoformat(end_date)
                except (TypeError, ValueError):
                    return {
                        "success": False,
                        "reason": "invalid_date_range",
                        "message": "Dates must use YYYY-MM-DD format.",
                    }

                if end <= start:
                    return {
                        "success": False,
                        "reason": "invalid_date_range",
                        "message": "end_date must be later than start_date.",
                    }

            missing_search_fields = []
            if (not recipient_hint and not search_keywords and not start_date and not end_date):
                missing_search_fields.append("recipient_hint_or_search_keywords_or_date_range")

            if missing_search_fields:
                return {
                    "success": False,
                    "reason": "missing_draft_search_fields",
                    "message": "Missing information required to identify the draft.",
                    "missing_fields": missing_search_fields,
                }

            query = build_gmail_query(
                search_scope="draft",
                start_date=start_date,
                end_date=end_date,
                search_keywords=search_keywords,
                recipient_hint=recipient_hint,
            )

            print("\nQuery")
            print(query)
            
            drafts_found = fetch_specific_gmail_drafts_full(
                access_token=access_token,
                max_results=max_results,
                query=query,
            )

            emails_found = drafts_found['drafts']

            if len(emails_found) == 1:
                selected_draft = emails_found[0]

                requested_new_recipient_email = arguments.get("new_recipient_email", "")
                requested_new_subject = arguments.get("new_subject", "")
                requested_new_body = arguments.get("new_body", "")
                
                if (
                        not requested_new_recipient_email
                        and not requested_new_subject
                        and not requested_new_body
                    ):
                    return {
                        "success": False,
                        "reason": "missing_update_fields",
                        "message": (
                            "No update fields were provided. Please specify at least one field "
                            "to update: recipient, subject, or body."
                        ),
                        "missing_fields": [
                            "new_recipient_email",
                            "new_subject",
                            "new_body",
                        ],
                    }

                new_recipient_email = requested_new_recipient_email or selected_draft["to"]
                new_subject = requested_new_subject or selected_draft["subject"]
                new_body = requested_new_body or selected_draft["body"]


                
                updated_draft = _update_and_verify_draft(
                    access_token=access_token,
                    draft=selected_draft,
                    body=new_body,
                    subject=new_subject,
                    recipient_email=new_recipient_email,
                )

                create_tool_state(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session=session,
                    state_type="gmail_active_draft",
                    payload={"active_draft": updated_draft},
                )

                return {
                    "success": True,
                    "new_subject": new_subject,
                    "new_body": new_body,
                    "new_recipient_email": new_recipient_email,
                    "draft": updated_draft,
                    "updated_fields": {
                        "recipient_email": bool(requested_new_recipient_email),
                        "subject": bool(requested_new_subject),
                        "body": bool(requested_new_body),
                    },
                }

            if len(emails_found) > 1:


                requested_new_recipient_email = arguments.get("new_recipient_email", "")
                requested_new_subject = arguments.get("new_subject", "")
                requested_new_body = arguments.get("new_body", "")

                payload = {
                    "drafts": emails_found,
                    "new_recipient_email": requested_new_recipient_email,
                    "new_subject": requested_new_subject,
                    "new_body": requested_new_body,
                    }
                
                create_tool_state(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session=session,
                    state_type="gmail_update_draft_selection",
                    payload=payload,
                )

                return ({"success": False,
                    "reason": "multiple_matching_drafts",
                    "message": "Multiple matching drafts found, please specify which draft you want to update",
                    "matching_drafts": emails_found,
                    "returned_count": drafts_found.get("returned_count", len(emails_found)),
                    "has_more": drafts_found.get("has_more", False),
                })

            if len(emails_found) == 0:
                return ({
                    "success": False,
                    "reason": "no_matching_draft",
                    "message": "No matching draft was found."
                })
