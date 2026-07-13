import base64

from datetime import date, datetime, time
from sqlalchemy.orm import Session
from email.utils import parseaddr, parsedate_to_datetime
from zoneinfo import ZoneInfo

from app.integrations.gmail.drafts import create_draft_reply, create_gmail_draft, fetch_gmail_draft_full, fetch_gmail_drafts, fetch_specific_gmail_drafts, fetch_specific_gmail_drafts_full, format_gmail_draft_full, send_gmail_draft, update_gmail_draft
from app.integrations.gmail.messages import build_gmail_search_query, fetch_full_specific_gmail_messages, fetch_latest_gmail_messages, fetch_specific_gmail_message_format_FSD, fetch_unread_gmail_messages, fetch_full_latest_gmail_messages, has_real_next_page, score_gmail_message_candidates, score_gmail_message_candidates_MORE, score_gmail_message_candidates_by_range, score_sent_gmail_message_candidates_by_range, search_latest_gmail_messages_for_metadata, fetch_specific_gmail_message_format_MORE
from app.integrations.gmail.search import build_gmail_query
from app.integrations.gmail.sent import fetch_sent_gmail_messages, fetch_specific_sent_gmail_messages
from app.repositories.conversation import create_tool_state, delete_tool_state, get_tool_payload
from app.services.external_auth_service import get_valid_google_access_token
from typing import Any


def format_gmail_message_metadata(
    message_data: list[dict[str, Any]] | dict[str, Any],
) -> list[dict[str, Any]] | dict[str, Any]:
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
            local_datetime = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=ZoneInfo("UTC"),
            ).astimezone(ZoneInfo("America/Bogota"))

            date_value = local_datetime.isoformat()

        formatted_emails.append({
            "from": header_values.get("from"),
            "subject": header_values.get("subject"),
            "date": date_value,
            "snippet": message.get("snippet"),
        })

    if isinstance(message_data, dict):
        return {
            **message_data,
            "emails": formatted_emails,
            "returned_count": len(formatted_emails),
        }

    return formatted_emails


# --------------GET UNREAD---------------
# region get unread
def get_unread_emails_tool(arguments: dict, user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    start_date = arguments.get("start_date", "")
    end_date = arguments.get("end_date", "")
    search_keywords = arguments.get("search_keywords", [])
    sender_hint = arguments.get("sender_hint", [])

    query = build_gmail_query(search_scope="unread",start_date=start_date, end_date=end_date, search_keywords=search_keywords, sender_hint=sender_hint, recipient_hint=None)

    print("\nQUERY USADA:")
    print(query)

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_unread_gmail_messages(access_token=access_token,max_results=max_results,query=query)

    message_list_output = format_gmail_message_metadata(message_data=message_list)
    print("\nCorreos encontrados de ese rango de fecha:")
    if isinstance(message_list_output, dict):
        print(message_list_output.get("returned_count", 0))
    else:
        print(len(message_list_output))

    if isinstance(message_list_output, dict):
        emails = message_list_output.get("emails", [])

        print(message_list_output.get("estimated_total"))
        return {
            "emails": emails,
            "returned_count": message_list_output.get(
                "returned_count",
                len(emails),
            ),
            "has_more": message_list_output.get("has_more", False),
            "next_page_token": message_list_output.get("next_page_token"),
        }

    return {
        "emails": message_list_output,
        "returned_count": len(message_list_output),
        "has_more": False,
        "next_page_token": None,
    }
# endregion

# --------------GET LATEST---------------
# region get latest
def get_latest_emails_tool(arguments: dict, user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_latest_gmail_messages(
        access_token=access_token, max_results=max_results
    )

    # [
    #   {
    #     "id": "18fabc1234567890",
    #     "threadId": "18fabc9999999999",
    #     "snippet": "Hola, te escribo para confirmar...",
    #     "payload": {
    #       "headers": [
    #         { "name": "From", "value": "Juan Pérez <juan@example.com>" },
    #         { "name": "Subject", "value": "Reunión de mañana" },
    #         { "name": "Date", "value": "Thu, 18 Jun 2026 09:30:00 -0500" }
    #       ]
    #     }
    #   },
    #   {
    #     "id": "18fabc9876543210",
    #     "threadId": "18fabc8888888888",
    #     "snippet": "Tu factura del mes ya está disponible...",
    #     "payload": {
    #       "headers": [
    #         { "name": "From", "value": "Facturación <billing@example.com>" },
    #         { "name": "Subject", "value": "Factura disponible" },
    #         { "name": "Date", "value": "Thu, 18 Jun 2026 08:10:00 -0500" }
    #       ]
    #     }
    #   }
    # ]


    message_list_output = format_gmail_message_metadata(message_data=message_list)

    if isinstance(message_list_output, dict):
        return message_list_output

    return {
        "emails": message_list_output,
        "has_more": False,
        "returned_count": len(message_list_output),
    }

# endregion

# --------------SEND---------------
# region send
# def gmail_send_email_message_tool(arguments: dict, user_id: int, session: Session):

#     recipient_email = arguments.get("recipient_email")
#     subject = arguments.get("subject")
#     body = arguments.get("body")


#     access_token=get_valid_google_access_token(user_id=user_id, session=session)
#     email_sent = gmail_send_email_message(
#         access_token=access_token,
#         recipient_email=recipient_email,
#         subject=subject,
#         body=body,
#     )

#     return email_sent
# endregion

# --------------SEARCH---------------
# region search
def gmail_search_email_message_tool(arguments: dict, user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    start_date = arguments.get("start_date", "")
    end_date = arguments.get("end_date", "")
    search_keywords = arguments.get("search_keywords", [])
    sender_hint = arguments.get("sender_hint", [])

    query = build_gmail_query(search_scope="received", start_date=start_date,end_date=end_date,search_keywords=search_keywords,sender_hint=sender_hint, recipient_hint=None)

    print("\nQuery:")
    print(query)

    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    emails_found = fetch_specific_gmail_message_format_FSD(access_token=access_token, query=query, max_results=max_results)

    print("\nEmails found:")
    print(len(emails_found["emails"]))
    print(emails_found["emails"])

    print("\nSearch info:")
    print(f"has_more: {emails_found["has_more"]}")
    print(f"returned_count: {emails_found["returned_count"]}")

    return emails_found

#endregion

# --------------DRAFT---------------
# region draft
def gmail_create_email_draft_tool(arguments:dict, user_id: int, session: Session):

    recipient_email = arguments.get("recipient_email")
    subject = arguments.get("subject")
    body = arguments.get("body")

    missing_fields = []

    if recipient_email is None:
        missing_fields.append("recipient_email")

    if subject is None:
        missing_fields.append("subject")

    if body is None:
        missing_fields.append("body")

    #si missing fields tiene algo, si es not empty
    if missing_fields:
        return {
            "created": False,
            "reason": "missing_required_fields",
            "missing_fields": missing_fields,
        }


    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    new_draft_message = create_gmail_draft(access_token=access_token, body=body, subject=subject, recipient_email=recipient_email)
    return new_draft_message


def gmail_create_multiple_email_drafts_tool(arguments: dict, user_id: int, session: Session):

    access_token = get_valid_google_access_token(user_id=user_id, session=session)

    to_create = arguments.get("to_create")
    to_create_list = arguments.get("to_create_list", [])

    if not isinstance(to_create_list, list):
        return {
            "created_count": 0,
            "failed_count": 0,
            "reason": "invalid_to_create_list",
            "message": "to_create_list must be a list."
        }

    results = []

    created_count = 0
    failed_count = 0
    for draft in to_create_list:
        missing_fields=[]

        recipient_email = draft.get("recipient_email")
        subject = draft.get("subject")
        body = draft.get("body")

        if not recipient_email:
            missing_fields.append("recipient_email")

        if not subject:
            missing_fields.append("subject")

        if not body:
            missing_fields.append("body")

        if missing_fields:
            failed_count +=1
            results.append({
                "created": False,
                "reason": "missing_required_fields",
                "missing_fields": missing_fields,
                "failed_email_fields":
                    {
                        "recipient_email": recipient_email,
                        "subject": subject,
                        "body": body

                    }
                })
            continue

        create_gmail_draft(access_token=access_token, body=body, subject=subject, recipient_email=recipient_email)
        created_count +=1

        results.append({
                "created": True,
                "created_email_fields":
                    {
                        "recipient_email": recipient_email,
                        "subject": subject,
                        "body":body

                    }
                })

    return ({
        "created_count": created_count,
        "failed_count": failed_count,
        "results": results
    })
    # {
    #   "needs_tool": true,
    #   "tool_name": "read_unread_emails",
    #   "arguments": {
    #     "to_create": 2,
    #     "to_create_list" : [
    #       {"recipient_email": "recipient@example.com",
    #       "subject": "Email subject",
    #       "body": "Email body"
    #       },
    #       {"recipient_email": "recipient@example.com",
    #       "subject": "Email subject",
    #       "body": "Email body"
    #       },
    #
    #      ]
    #   }
    # }


def gmail_get_drafted_emails_tool(arguments: dict,user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 5)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    return fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=max_results,
        query="",
    )


def gmail_search_drafted_emails_tool(arguments: dict, user_id: int, session: Session, conversation_id: int | None = None):
    max_results = min(
        max(int(arguments.get("max_results", 5)), 1),
        15,
    )
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

    print("\nQuery:")
    print(query)

    access_token = get_valid_google_access_token(user_id=user_id, session=session)

    draft_results = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    if conversation_id is not None and draft_results.get("drafts"):
        delete_tool_state(user_id=user_id,conversation_id=conversation_id, session=session)

        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            payload=draft_results["drafts"],
            session=session,
        )

    return draft_results


def gmail_send_drafted_email_tool(arguments:dict, user_id: int, session: Session, conversation_id: int):

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    selected_result_index = arguments.get("selected_result_index")

    requested_draft_count = arguments.get("requested_draft_count", 1)

    if requested_draft_count is None:
        return ({
            "sent": False,
            "reason": "multiple_draft_send_not_supported",
            "requested_draft_count": None
        })

    requested_draft_count = int(requested_draft_count)

    if requested_draft_count > 1:
        return ({
            "sent": False,
            "reason": "multiple_draft_send_not_supported",
            "requested_draft_count": requested_draft_count
        })

    if not requested_draft_count:
        return ({
            "sent": False,
            "reason": "incorrect_draft_send",
            "requested_draft_count": 0
        })

    if selected_result_index is not None:
        selected_result_index = int(selected_result_index)

    #si hay una lista en tool_state y se elige entre una
    if selected_result_index is not None:
        print("\nSELECTED RESULT INDEX ->")
        print(selected_result_index)
        tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

        if tool_payload is None:
            return {
                "sent": False,
                "reason": "missing_tool_state",
                "message": "No previous draft selection was found."
            }

        if selected_result_index < 1 or selected_result_index> len(tool_payload): # type: ignore # noqa: F821
            return ({
                "sent": False,
                "reason": "invalid_selected_result_index",
                "message": "Selected draft index is out of range",
                "available_drafts": tool_payload # type: ignore  # noqa: F821
            })

        selected_draft = tool_payload[selected_result_index-1] # pyright: ignore[reportUnboundVariable]
        print("\nDRAFT SELECTED ->")
        print(selected_draft)


        send_gmail_draft(draft_id=tool_payload[selected_result_index-1]["draft_id"], access_token=access_token) # type: ignore
        delete_tool_state(user_id=user_id, conversation_id=conversation_id, session=session)
        return ({
            "sent": True,
            "draft_id":selected_draft["draft_id"],  # type: ignore
            "selected_draft": selected_draft,  # type: ignore
        })


    selection_type = arguments.get("selection_type")

    #si es un correo reciente, ultimo, penultimo
    if selection_type == "recent_draft":

        recent_draft_index = arguments.get("recent_draft_index")

        if recent_draft_index is None:
            return {
                "sent": False,
                "reason": "missing_recent_draft_index",
                "message": "Missing recent draft index."
            }

        recent_draft_position = int(recent_draft_index)
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
                "sent": False,
                "reason": "invalid_recent_draft_index",
                "message": "Requested recent draft index is out of range.",
                "available_drafts": last_drafted_emails,
            }

        selected_draft = last_drafted_emails[recent_draft_index]
        print("DRAFT SELECCIONADO")
        print(selected_draft)

        send_gmail_draft(draft_id=selected_draft["id"], access_token=access_token)
        return ({
            "sent": True,
            "draft_id":selected_draft["id"],
            "selected_draft": selected_draft,
            })


    max_results = min(
        max(int(arguments.get("max_results", 5)), 1),
        15,
    )
    start_date = arguments.get("start_date")
    end_date = arguments.get("end_date")
    recipient_hint = arguments.get("recipient_hint", [])
    search_keywords = arguments.get("search_keywords", [])

    if not recipient_hint and not search_keywords and not start_date and not end_date:
        return {
            "sent": False,
            "reason": "missing_draft_search_fields",
            "message": "Missing information required to identify the draft."
        }

    query = build_gmail_query(
        search_scope="draft",
        start_date=start_date,
        end_date=end_date,
        search_keywords=search_keywords,
        recipient_hint=recipient_hint,
    )

    print("\nQuery:")
    print(query)

    drafts_found = fetch_specific_gmail_drafts(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    emails_found = drafts_found["drafts"]


    print('\nDRAFT MATCHES FOUND:')
    print(emails_found)

    if emails_found is None:
        raise ValueError("Draft search failed")

    if len(emails_found) == 0:
        return ({
            "sent": False,
            "reason": "no_matching_draft",
            "message": "No matching draft was found."
        })

    if len(emails_found) > 1:
        delete_tool_state(user_id=user_id,conversation_id=conversation_id, session=session)
        for item in emails_found:
            for key, value in item.items():
                print(key, value, type(value))
            print("-----------------------------")
        create_tool_state(user_id=user_id, conversation_id=conversation_id, payload=emails_found, session=session)

        return ({
            "sent": False,
            "reason": "multiple_matching_drafts",
            "message": "Multiple matching drafts found, please specify which draft you want to send",
            "matching_drafts_found": emails_found,
            "returned_count": drafts_found.get("returned_count", len(emails_found)),
            "has_more": drafts_found.get("has_more", False),
        })

    if len(emails_found) == 1:
    #si la busqueda fue especifica y se encontro uno correo.
        selected_draft = emails_found[0]
        send_gmail_draft(draft_id=selected_draft["draft_id"], access_token=access_token)
        return ({
            "sent": True,
            "draft_id":selected_draft["draft_id"],
            "selected_draft": selected_draft,
            })


def gmail_update_email_draft_tool(user_id: int, session: Session, arguments: dict, conversation_id: int):

    access_token = get_valid_google_access_token(user_id=user_id,session=session,)
    recent_draft_index = arguments.get("recent_draft_index")
    selection_type = arguments.get("selection_type")

    if selection_type not in {"active_draft", "recent_draft", "specific_draft"}:
        return {
            "updated": False,
            "reason": "invalid_selection_type",
            "message": "A valid draft selection type is required.",
        }

    if selection_type == "active_draft":
        tool_payload = get_tool_payload(
            user_id=user_id,
            session=session,
            conversation_id=conversation_id,
        )

        if tool_payload is None or "active_draft" not in tool_payload:
            return {
                "updated": False,
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
                "updated": False,
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

        update_gmail_draft(
            access_token=access_token,
            body=new_body,
            subject=new_subject,
            recipient_email=new_recipient_email,
            draft_id=selected_draft["draft_id"],
            )

        updated_draft = {
            **selected_draft,
            "to": new_recipient_email,
            "subject": new_subject,
            "body": new_body,
        }

        delete_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
        )
        create_tool_state(
            user_id=user_id,
            conversation_id=conversation_id,
            session=session,
            payload={"active_draft": updated_draft},
        )

        return {
            "updated": True,
            "new_recipient_email": new_recipient_email,
            "new_subject": new_subject,
            "new_body": new_body,
            "selected_draft": updated_draft,
            "updated_fields": {
                "recipient_email": bool(requested_new_recipient_email),
                "subject": bool(requested_new_subject),
                "body": bool(requested_new_body),
            },
        }

    if selection_type == "recent_draft":

        recent_draft_index = arguments.get("recent_draft_index")

        if recent_draft_index is None:
            return {
                "updated": False,
                "reason": "missing_recent_draft_index",
                "message": "Missing recent draft index."
            }

        if recent_draft_index is not None:
            try:
                recent_draft_position = int(recent_draft_index)
            except (TypeError, ValueError):
                return {
                    "updated": False,
                    "reason": "invalid_recent_draft_index",
                    "message": "Recent draft index must be a positive integer.",
                }

            if recent_draft_position < 1:
                return {
                    "updated": False,
                    "reason": "invalid_recent_draft_index",
                    "message": "Recent draft index must be a positive integer.",
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
                    "updated": False,
                    "reason": "invalid_recent_draft_index",
                    "message": "Requested recent draft index is out of range.",
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
                    "updated": False,
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

            update_gmail_draft(
                access_token=access_token,
                body=new_body,
                recipient_email=new_recipient_email,
                subject=new_subject,
                draft_id=selected_draft["draft_id"],
            )

            updated_draft = {
                **selected_draft,
                "to": new_recipient_email,
                "subject": new_subject,
                "body": new_body,
            }

            delete_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
            )
            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                payload={"active_draft": updated_draft},
            )

            return {
                "updated": True,
                "new_recipient_email": new_recipient_email,
                "new_subject": new_subject,
                "new_body": new_body,
                "selected_draft": updated_draft,
                "updated_fields": {
                    "recipient_email": bool(requested_new_recipient_email),
                    "subject": bool(requested_new_subject),
                    "body": bool(requested_new_body),
                },
            }

    if selection_type == "specific_draft":

        selected_result_index = arguments.get("selected_result_index")

        if selected_result_index is not None:
            try:
                selected_result_index = int(selected_result_index)
            except (TypeError, ValueError):
                return {
                    "updated": False,
                    "reason": "invalid_selected_result_index",
                    "message": "Selected draft index must be a positive integer.",
                }

            tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

            if tool_payload is None:
                return {
                    "updated": False,
                    "reason": "missing_tool_state",
                    "message": "No previous draft selection was found."
                }

            if "drafts" not in tool_payload:
                return {
                    "updated": False,
                    "reason": "invalid_tool_state",
                    "message": "Previous draft selection is invalid.",
                }

            drafts_to_choose = tool_payload["drafts"]

            if selected_result_index < 1 or selected_result_index > len(drafts_to_choose):
                return {
                    "updated": False,
                    "reason": "invalid_selected_result_index",
                    "message": "Selected draft index is out of range.",
                    "available_drafts": drafts_to_choose,
                }

            selected_draft = drafts_to_choose[selected_result_index - 1]

            requested_new_recipient_email = tool_payload.get("new_recipient_email", "")
            requested_new_subject = tool_payload.get("new_subject", "")
            requested_new_body = tool_payload.get("new_body", "")

            if (
                not requested_new_recipient_email
                and not requested_new_subject
                and not requested_new_body
            ):
                return {
                    "updated": False,
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

            update_gmail_draft(
                access_token=access_token,
                body=new_body,
                subject=new_subject,
                recipient_email=new_recipient_email,
                draft_id=selected_draft["draft_id"],
            )

            updated_draft = {
                **selected_draft,
                "to": new_recipient_email,
                "subject": new_subject,
                "body": new_body,
            }

            delete_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
            )
            create_tool_state(
                user_id=user_id,
                conversation_id=conversation_id,
                session=session,
                payload={"active_draft": updated_draft},
            )

            return {
                "updated": True,
                "new_subject": new_subject,
                "new_body": new_body,
                "new_recipient_email": new_recipient_email,
                "selected_draft": updated_draft,
                "updated_fields": {
                    "recipient_email": bool(requested_new_recipient_email),
                    "subject": bool(requested_new_subject),
                    "body": bool(requested_new_body),
                },
            }

        if selected_result_index is None:
            try:
                max_results = min(max(int(arguments.get("max_results", 5)), 1), 15)
            except (TypeError, ValueError):
                return {
                    "updated": False,
                    "reason": "invalid_max_results",
                    "message": "max_results must be an integer between 1 and 15.",
                }

            start_date = arguments.get("start_date")
            end_date = arguments.get("end_date")
            recipient_hint = arguments.get("recipient_hint", [])
            search_keywords = arguments.get("search_keywords", [])

            if bool(start_date) != bool(end_date):
                return {
                    "updated": False,
                    "reason": "incomplete_date_range",
                    "message": "start_date and end_date must be provided together.",
                }

            if start_date and end_date:
                try:
                    start = date.fromisoformat(start_date)
                    end = date.fromisoformat(end_date)
                except (TypeError, ValueError):
                    return {
                        "updated": False,
                        "reason": "invalid_date_range",
                        "message": "Dates must use YYYY-MM-DD format.",
                    }

                if end <= start:
                    return {
                        "updated": False,
                        "reason": "invalid_date_range",
                        "message": "end_date must be later than start_date.",
                    }

            missing_search_fields = []
            if (not recipient_hint and not search_keywords and not start_date and not end_date):
                missing_search_fields.append("recipient_hint_or_search_keywords_or_date_range")

            if missing_search_fields:
                return {
                    "updated": False,
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
                        "updated": False,
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


                
                update_gmail_draft(
                    access_token=access_token,
                    body=new_body,
                    subject=new_subject,
                    recipient_email=new_recipient_email,
                    draft_id=emails_found[0]["draft_id"],
                    )
                
                updated_draft = {
                    **selected_draft,
                    "to": new_recipient_email,
                    "subject": new_subject,
                    "body": new_body,
                }

                delete_tool_state(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session=session,
                )
                create_tool_state(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    session=session,
                    payload={"active_draft": updated_draft},
                )

                return {
                    "updated": True,
                    "new_subject": new_subject,
                    "new_body": new_body,
                    "new_recipient_email": new_recipient_email,
                    "selected_draft": updated_draft,
                    "updated_fields": {
                        "recipient_email": bool(requested_new_recipient_email),
                        "subject": bool(requested_new_subject),
                        "body": bool(requested_new_body),
                    },
                }

            if len(emails_found) > 1:


                delete_tool_state(user_id=user_id,conversation_id=conversation_id, session=session)
                
                requested_new_recipient_email = arguments.get("new_recipient_email", "")
                requested_new_subject = arguments.get("new_subject", "")
                requested_new_body = arguments.get("new_body", "")

                payload = {
                    "drafts": emails_found,
                    "new_recipient_email": requested_new_recipient_email,
                    "new_subject": requested_new_subject,
                    "new_body": requested_new_body,
                    }
                
                create_tool_state(user_id=user_id, conversation_id=conversation_id, session=session, payload=payload)

                return ({"updated": False,
                    "reason": "multiple_matching_drafts",
                    "message": "Multiple matching drafts found, please specify which draft you want to update",
                    "matching_drafts_found": emails_found,
                    "returned_count": drafts_found.get("returned_count", len(emails_found)),
                    "has_more": drafts_found.get("has_more", False),
                })

            if len(emails_found) == 0:
                return ({
                    "updated": False,
                    "reason": "no_matching_draft",
                    "message": "No matching draft was found."
                })



def gmail_create_reply_draft_tool(arguments: dict, user_id: int, session: Session, conversation_id: int):
    access_token = get_valid_google_access_token(user_id=user_id,session=session)
    reply_body = arguments.get("reply_body", "")

    selection_type = arguments.get("selection_type")

    if selection_type not in {"recent_email", "specific_email"}:
        return {
            "created": False,
            "reason": "invalid_selection_type",
            "message": "A valid email selection type is required.",
        }

    if selection_type == "recent_email":
        if not reply_body:
            return {
                "created": False,
                "reason": "missing_body",
                "message": "Body is required for the new draft content, request it to the user",
            }

        recent_email_position = arguments.get("recent_email_position", 1)

        try:
            recent_email_position = int(recent_email_position)
        except (TypeError, ValueError):
            return {
                "created": False,
                "reason": "invalid_recent_email_position",
                "message": "Recent email position must be a positive integer.",
            }

        if recent_email_position < 1:
            return {
                "created": False,
                "reason": "invalid_recent_email_position",
                "message": "Recent email position must be at least 1.",
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
                "created": False,
                "reason": "invalid_recent_email_position",
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

        return {
            "created": True,
            "draft_id": created_draft["id"],
            "message_id": created_draft["message"]["id"],
            "thread_id": created_draft["message"]["threadId"],
            "recipient_email": reply_context["recipient_email"],
            "subject": reply_context["subject"],
        }

    if selection_type == "specific_email":

        selected_result_position = arguments.get("selected_result_position")
        print("\nSelected result position mode:")
        if selected_result_position is not None:
            try:
                selected_result_position = int(selected_result_position)
            except (TypeError, ValueError):
                return {
                    "created": False,
                    "reason": "invalid_selected_result_position",
                    "message": "Selected email position must be a positive integer.",
                }

            tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

            if tool_payload is None:
                return {
                    "created": False,
                    "reason": "missing_tool_state",
                }

            if "emails_found" not in tool_payload:
                return {
                    "created": False,
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
                    "created": False,
                    "reason": "invalid_selected_result_position",
                    "message": "Selected email position is out of range.",
                }

            reply_body = arguments.get("reply_body") or tool_payload.get("reply_body", "")

            if not reply_body:
                return {
                    "created": False,
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
            print("\nDeleted tool state!")
            return {
                "created": True,
                "draft_id": created_draft["id"],
                "message_id": created_draft["message"]["id"],
                "thread_id": created_draft["message"]["threadId"],
                "recipient_email": selected_match["recipient_email"],
                "subject": selected_match["subject"],
            }

        if not reply_body:
            return {
                "created": False,
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
                "created": False,
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

            return {
            "created": True,
            "draft_id": created_draft["id"],
            "message_id": created_draft["message"]["id"],
            "thread_id": created_draft["message"]["threadId"],
            "recipient_email": emails_fetched[0]["recipient_email"],
            "subject": emails_fetched[0]["subject"],
        }

        if len(emails_fetched) >1:
            delete_tool_state(user_id=user_id, conversation_id=conversation_id,session=session)
            create_tool_state(
                payload={
                    "emails_found": emails_fetched,
                    "reply_body": reply_body,
                },
                user_id=user_id,
                session=session,
                conversation_id=conversation_id
            )

            return({
                "created": False,
                "reason": "multiple_matching_emails",
                "message": "Multiple matching emails found, please specify which email you want to reply to.",
                "matching_emails": emails_fetched,
                "returned_count": email_results["returned_count"],
                "has_more": email_results["has_more"],
            })


# endregion

# --------------READ---------------
# region read

def gmail_read_latest_email_tool(user_id: int, session: Session, arguments: dict,):
    access_token = get_valid_google_access_token(user_id=user_id,session=session,)

    recent_email_position = arguments.get("recent_email_position")

    if recent_email_position:
        recent_email_position = int(recent_email_position)

        if recent_email_position < 1:
            return {
                "found": False,
                "reason": "invalid_recent_email_position",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        latest_emails = fetch_full_latest_gmail_messages(
            access_token=access_token,
            max_results=recent_email_position,
        )

        if recent_email_position > len(latest_emails):
            return {
                "found": False,
                "reason": "recent_email_position_out_of_range",
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        email = format_gmail_email(
            email_requested=latest_emails[recent_email_position-1]
        )

        return {
            "found": True,
            "emails": [email],
            "returned_count": 1,
            "has_more": False,
        }

    max_results = arguments.get("max_results", 1)
    max_results = min(max(int(max_results), 1), 2)

    latest_emails = fetch_full_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )

    emails_list = []

    for email in latest_emails:
        emails_list.append(format_gmail_email(email_requested=email))

    return {
        "found": bool(emails_list),
        "emails": emails_list,
        "returned_count": len(emails_list),
        "has_more": False,
    }


def format_gmail_email(email_requested: dict):

    def find_text_body(payload: dict) -> str | None:
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data")

        if mime_type == "text/plain" and body_data:
            return body_data

        for part in payload.get("parts", []):
            body_data = find_text_body(part)

            if body_data:
                return body_data

        return None

    headers = email_requested.get("payload", {}).get("headers", [])

    date = ""
    subject = ""
    who_from = ""

    for header in headers:
        header_name = header.get("name", "").lower()
        header_value = header.get("value", "")

        if header_name == "subject":
            subject = header_value
        elif header_name == "from":
            who_from = header_value
        elif header_name == "date":
            date = header_value

    payload = email_requested.get("payload", {})
    body_data = find_text_body(payload)

    if body_data:
        padded_body = body_data + "=" * (-len(body_data) % 4)
        decoded_body = base64.urlsafe_b64decode(padded_body)
        body = decoded_body.decode("utf-8", errors="replace")
    else:
        body = email_requested.get("snippet", "")

    return {
        "from": who_from,
        "subject": subject,
        "date": date,
        "body": body,
    }


def format_gmail_email_candidates(emails: list[dict],) -> list[dict]:

    utc_timezone = ZoneInfo("UTC")
    user_timezone = ZoneInfo("America/Bogota")

    candidates = []

    for position, email in enumerate(emails, start=1):
        headers = {
            header.get("name", "").lower(): header.get("value", "")
            for header in email.get("payload", {}).get("headers", [])
        }

        date_value = headers.get("date", "")
        internal_date = email.get("internalDate")

        if internal_date:
            try:
                local_datetime = datetime.fromtimestamp(
                    int(internal_date) / 1000,
                    tz=utc_timezone,
                ).astimezone(user_timezone)

                date_value = local_datetime.isoformat()
            except (TypeError, ValueError, OverflowError):
                pass

        elif date_value:
            try:
                parsed_date = parsedate_to_datetime(date_value)

                if parsed_date.tzinfo is None:
                    parsed_date = parsed_date.replace(
                        tzinfo=utc_timezone,
                    )

                date_value = parsed_date.astimezone(
                    user_timezone,
                ).isoformat()
            except (TypeError, ValueError, OverflowError):
                pass

        candidates.append({
            "position": position,
            "from": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            "date": date_value,
            "snippet": email.get("snippet", ""),
        })

    return candidates


def gmail_read_specific_email_tool(arguments: dict, session: Session, user_id: int,conversation_id: int):

    requested_email_count = arguments.get("requested_email_count", 1)

    selected_result_position = arguments.get("selected_result_position", "")

    max_results = arguments.get("max_results", 3)
    start_date = arguments.get("start_date", "")
    end_date = arguments.get("end_date", "")
    search_keywords = arguments.get("search_keywords", [])
    sender_hint = arguments.get("sender_hint", [])


    if requested_email_count > 1:
        return {
            "read": False,
            "reason": "multiple_email_read_not_supported",
            "message": (
                "Only one complete email can be read per request. "
                "Ask the user which email they want to read first."
            ),
            "requested_email_count": requested_email_count,
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    if selected_result_position:
        selected_result_position = int(selected_result_position)

        tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

        if not isinstance(tool_payload, dict) or "emails" not in tool_payload:
            return {
                "read": False,
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
                "read": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected email position is out of range.",
                "available_positions": len(emails_to_choose),
                "emails": [],
                "returned_count": 0,
                "has_more": False,
            }

        email_selected = emails_to_choose[selected_result_position - 1]
        formatted_email = format_gmail_email(email_requested=email_selected)
        delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)

        return {
            "read": True,
            "emails": [formatted_email],
            "returned_count": 1,
            "has_more": False,
        }

    query = build_gmail_query(search_scope="received", start_date=start_date,end_date=end_date,search_keywords=search_keywords,sender_hint=sender_hint)

    print("\nQuery:")
    print(query)
    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    emails_found = fetch_full_specific_gmail_messages(access_token=access_token,max_results=max_results,query=query)

    if emails_found is None:
        return {
            "read": False,
            "reason": "email_not_found",
            "message": "No email matched the provided query.",
            "emails": [],
            "returned_count": 0,
            "has_more": False,
        }

    print("\nEmails Found")
    for index, email in enumerate(emails_found, start=1):
        headers = {
            header.get("name", "").lower(): header.get("value", "")
            for header in email.get("payload", {}).get("headers", [])
        }

        print(f"\n--- EMAIL {index} ---")
        print(f"ID: {email.get('id')}")
        print(f"From: {headers.get('from')}")
        print(f"To: {headers.get('to')}")
        print(f"Subject: {headers.get('subject')}")
        print(f"Date: {headers.get('date')}")
        print(f"Snippet: {email.get('snippet')}")


    if len(emails_found) > 1:
        matching_email_summaries = format_gmail_email_candidates(emails_found)
        delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)
        create_tool_state(
            user_id=user_id,
            session=session,
            conversation_id=conversation_id,
            payload={"emails": emails_found},
        )

        return {
            "read": False,
            "reason": "multiple_matching_emails",
            "message": "Multiple emails matched the query. Please specify which one you want to read.",
            "matching_emails": matching_email_summaries,
            "returned_count": len(matching_email_summaries),
            "has_more": False,
        }

    if len(emails_found) == 1:
        formatted_email = format_gmail_email(email_requested=emails_found[0])

        return {
            "read": True,
            "emails": [formatted_email],
            "returned_count": 1,
            "has_more": False,
        }

# endregion

#---------------SENT-------------
# region sent

def gmail_get_sent_emails_tool(arguments: dict ,user_id:int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 15)
    access_token = get_valid_google_access_token(user_id=user_id,session=session)
    emails_found = fetch_sent_gmail_messages(access_token=access_token, max_results=max_results)

    if not emails_found:
        return ({
            "emails_found": None
        })

    return emails_found

def gmail_search_sent_emails_tool(arguments: dict, user_id: int, session: Session):
    max_results = arguments.get("max_results", 3)
    start_date = arguments.get("start_date", "")
    end_date = arguments.get("end_date", "")
    search_keywords = arguments.get("search_keywords", [])
    recipient_hint = arguments.get("recipient_hint", [])

    query = build_gmail_query(search_scope="sent",start_date=start_date, end_date=end_date, search_keywords=search_keywords, recipient_hint=recipient_hint, sender_hint= None)

    print("\nQuery:")
    print(query)

    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    emails_found = fetch_specific_sent_gmail_messages(access_token=access_token, query=query, max_results=max_results)

    print("\nEmails found:")
    print(len(emails_found["emails"]))

    return emails_found
# endregion

#---------------EXTRAS-------------
# region extras
# def format_gmail_email_candidates(emails_found: list[dict]) -> list[dict]:
#     formatted_emails = []

#     for position, email in enumerate(emails_found, start=1):
#         header_values = {}

#         for header in email.get("payload", {}).get("headers", []):
#             header_name = header.get("name", "").lower()

#             if header_name in {"from", "subject", "date"}:
#                 header_values[header_name] = header.get("value", "")

#         formatted_emails.append({
#             "position": position,
#             "from": header_values.get("from", ""),
#             "subject": header_values.get("subject", ""),
#             "date": header_values.get("date", ""),
#             "snippet": email.get("snippet", ""),
#         })

#     return formatted_emails

def extract_gmail_reply_context(emails: list, email_index: int):
    response_headers = emails[email_index]["payload"]["headers"]

    from_email = ""
    reply_to_email = ""
    subject = ""
    references = ""
    original_message_id = ""

    for header in response_headers:
        header_name = header["name"].lower()
        header_value = header["value"]

        if header_name == "from":
            _, from_email = parseaddr(header_value)
        elif header_name == "reply-to":
            _, reply_to_email = parseaddr(header_value)
        elif header_name == "subject":
            subject = header_value
        elif header_name == "references":
            references = header_value
        elif header_name == "message-id":
            original_message_id = header_value

    recipient_email = reply_to_email or from_email
    references = f"{references} {original_message_id}".strip()

    return {
        "threadId": emails[email_index]["threadId"],
        "original_message_id": original_message_id,
        "references": references,
        "recipient_email": recipient_email,
        "subject": subject,
    }

# endregion

