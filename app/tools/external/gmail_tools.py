import base64

from sqlalchemy.orm import Session
from email.utils import parseaddr

from app.integrations.gmail.drafts import create_draft_reply, create_gmail_draft, fetch_gmail_drafts, normalize_text, search_gmail_drafts, search_gmail_drafts_no_snippet, send_gmail_draft, update_gmail_draft
from app.integrations.gmail.messages import build_gmail_search_query, fetch_full_specific_gmail_messages, fetch_latest_gmail_messages, fetch_specific_gmail_message_format_FSD, fetch_unread_gmail_messages, fetch_full_latest_gmail_messages, score_gmail_message_candidates, score_gmail_message_candidates_MORE, search_latest_gmail_messages_for_metadata, fetch_specific_gmail_message_format_MORE
from app.repositories.conversation import create_tool_state, delete_tool_state, get_tool_payload
from app.services.external_auth_service import get_valid_google_access_token


def format_gmail_message_metadata(message_list: list):
    message_list_output = []

    for message in message_list:
        headers = message["payload"]["headers"]

        from_value = None
        date_value = None
        subject_value = None

        snippet = message["snippet"]

        for header in headers:
            header_name = header.get("name", "").lower()
            if header_name == "from":
                from_value = header["value"]
            if header_name == "subject":
                subject_value = header["value"]
            if header_name == "date":
                date_value = header["value"]

        message_list_output.append(
            {"from": from_value, "subject": subject_value, "date": date_value, "snippet": snippet}
        )

    return message_list_output


# --------------GET UNREAD---------------
# region get unread
def get_unread_emails_tool(arguments: dict, user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 5)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    message_list = fetch_unread_gmail_messages(
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

    message_list_output = format_gmail_message_metadata(message_list=message_list)
    return message_list_output
# endregion

# --------------GET LATEST---------------
# region get latest
def get_latest_emails_tool(arguments: dict, user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 5)
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


    message_list_output = format_gmail_message_metadata(message_list=message_list)
    return message_list_output

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
    sender_hint = arguments.get("sender_hint", "")
    search_keywords = arguments.get("search_keywords", [])
    requested_max_results = int(arguments.get("max_results", 10))
    max_results = min(max(requested_max_results, 1), 50)
    date_hint = arguments.get("date_hint")

    normalized_sender_words = set(normalize_text(sender_hint).split())
    search_keywords = [
        keyword
        for keyword in search_keywords
        if normalize_text(keyword) not in normalized_sender_words
    ]

    query = build_gmail_search_query(
        sender_hint=sender_hint,
        search_keywords=search_keywords,
        date_hint=date_hint,
    )


    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    emails_found = fetch_specific_gmail_message_format_FSD(access_token=access_token, query=query, max_results=max_results)

    emails_found_scored = score_gmail_message_candidates(emails_found=emails_found, sender_hint=sender_hint, search_keywords=search_keywords, date_hint=date_hint)

    print("\nEmails found")
    print(emails_found_scored)
    return emails_found_scored

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
    draft_email = fetch_gmail_drafts(access_token=access_token,max_results=max_results)
    return draft_email


def gmail_search_drafted_emails_tool(arguments: dict, user_id: int, session: Session):
    recipient_hint = arguments.get("recipient_hint","")
    subject_keywords = arguments.get("subject_keywords",[])
    snippet_keywords = arguments.get("snippet_keywords",[])
    max_results = arguments.get("max_results",10)

    access_token = get_valid_google_access_token(user_id=user_id, session=session)

    response = search_gmail_drafts(access_token=access_token, max_results=max_results, recipient_hint=recipient_hint, subject_keywords=subject_keywords, snippet_keywords=snippet_keywords)


    print(response)
    return response


def gmail_send_drafted_email_tool(arguments:dict, user_id: int, session: Session, conversation_id: int):

    access_token = get_valid_google_access_token(user_id=user_id, session=session)


    selected_result_index = arguments.get("selected_result_index")

    if selected_result_index is not None:
        selected_result_index = int(selected_result_index)

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

    if selection_type == "recent_draft":

        recent_draft_index = arguments.get("recent_draft_index")

        if recent_draft_index is None:
            return {
                "sent": False,
                "reason": "missing_recent_draft_index",
                "message": "Missing recent draft index."
            }
        
        recent_draft_index = int(recent_draft_index)

        max_results = max(recent_draft_index + 1, 1)


        last_drafted_emails = gmail_get_drafted_emails_tool(user_id=user_id, session=session, arguments={
            "max_results": max_results
        })

        # la posición que pidio el usuario existe en esta lista?
        # recent_draft_index = 0  valido
        # recent_draft_index = 1  valido
        # recent_draft_index = 2  invalido
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


    
    recipient_hint = arguments.get("recipient_hint","")
    subject_keywords = arguments.get("subject_keywords",[])
    snippet_keywords = arguments.get("snippet_keywords",[])
    max_results = arguments.get("max_results",10)
    
    emails_found = search_gmail_drafts(access_token=access_token, max_results=max_results, recipient_hint=recipient_hint, subject_keywords=subject_keywords, snippet_keywords=snippet_keywords)


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

        for item in emails_found:
            for key, value in item.items():
                print(key, value, type(value))
            print("-----------------------------")
        create_tool_state(user_id=user_id, conversation_id=conversation_id, payload=emails_found, session=session)

        return ({
            "sent": False,
            "reason": "multiple_matching_drafts",
            "message": "Multiple matching drafts found, please specify which draft you want to send",
            "matching_drafts_found": emails_found
        })
        
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

    if selection_type == "recent_draft":

        recent_draft_index = arguments.get("recent_draft_index")

        if recent_draft_index is None:
            return {
                "updated": False,
                "reason": "missing_recent_draft_index",
                "message": "Missing recent draft index."
            }

        if recent_draft_index is not None:

            missing_search_fields = []

            recipient_email = arguments.get("recipient_email")
            if recipient_email is None:
                missing_search_fields.append("recipient_email")

            subject = arguments.get("subject")
            if subject is None:
                missing_search_fields.append("subject")

            body = arguments.get("body")
            if body is None:
                missing_search_fields.append("body")

            if missing_search_fields:
                return ({
                    "updated": False,
                    "reason": "missing_required_fields",
                    "missing_fields": missing_search_fields,
                })

            recent_draft_index = int(recent_draft_index)

            max_results = max(recent_draft_index + 1, 1)

            last_drafted_emails = gmail_get_drafted_emails_tool(user_id=user_id, session=session, arguments={
                "max_results": max_results
            })
            # la posición que pidio el usuario existe en esta lista?
            # recent_draft_index = 0  valido
            # recent_draft_index = 1  valido
            # recent_draft_index = 2  invalido
            if recent_draft_index < 0 or recent_draft_index >= len(last_drafted_emails):
                return {
                    "sent": False,
                    "reason": "invalid_recent_draft_index",
                    "message": "Requested recent draft index is out of range.",
                    "available_drafts": last_drafted_emails,
                }

            print("funciona__+_+")
            selected_draft = last_drafted_emails[recent_draft_index]
            update_gmail_draft(access_token=access_token, body=body, recipient_email=recipient_email, subject=subject, draft_id=selected_draft["id"])
            return ({
                "updated": True,
                "new_recipient_email": recipient_email,
                "new_subject": subject,
                "new_body": body
            })
            
    if selection_type == "specific_draft":

        selected_result_index = arguments.get("selected_result_index")

        if selected_result_index:
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
            
            selected_draft = tool_payload["emails_found"][selected_result_index-1]
            update_gmail_draft(
                access_token=access_token,
                body=tool_payload["new_body"],
                subject=tool_payload["new_subject"],
                recipient_email=tool_payload["new_recipient_email"],
                draft_id=selected_draft["draft_id"],
                )
            delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)
            return ({
                "updated": True,
                "new_subject": tool_payload["new_subject"],
                "new_body": tool_payload["new_body"],
                "new_recipient_email": tool_payload["new_recipient_email"]
            })


        max_results = arguments.get("max_results", 10)

        missing_search_fields = []

        to_change_recipient_email = arguments.get("to_change_recipient_email", "")
        if to_change_recipient_email is None:
            missing_search_fields.append("to_change_recipient_email")
        
        to_change_subject_keywords = arguments.get("to_change_subject_keywords", [])
        if to_change_subject_keywords is None:
            missing_search_fields.append("to_change_subject_keywords")

        missing_replacement_fields = []

        new_recipient_email = arguments.get("new_recipient_email", "")
        if not new_recipient_email:
            missing_replacement_fields.append("new_recipient_email")

        new_subject = arguments.get("new_subject", "")
        if not new_subject:
            missing_replacement_fields.append("new_subject")

        new_body = arguments.get("new_body", "")
        if not new_body:
            missing_replacement_fields.append("new_body")

        print("\nMISSING SERCH FIELDS:")
        print(missing_search_fields)

        print("\nMISSING REPLACEMENT FIELDS:")
        print(missing_replacement_fields)
        if missing_search_fields and missing_replacement_fields:
            return {
                "updated": False,
                "reason": "missing_search_and_replacement_fields",
                "message": "Missing fields required to identify and update the draft.",
                "missing_search_fields": missing_search_fields,
                "missing_replacement_fields": missing_replacement_fields,
            }

        if missing_search_fields:
            return {
                "updated": False,
                "reason": "missing_draft_search_fields",
                "message": "Missing information required to identify the draft.",
                "missing_fields": missing_search_fields,
            }

        if missing_replacement_fields:
            return {
                "updated": False,
                "reason": "missing_draft_replacement_fields",
                "message": "Missing fields required for the new draft content.",
                "missing_fields": missing_replacement_fields,
            }
                


        emails_found = search_gmail_drafts_no_snippet(access_token=access_token, recipient_hint=to_change_recipient_email, subject_keywords=to_change_subject_keywords, max_results=max_results)

        print("\n EMAILS ENCONTRADOS:")
        for index, draft in enumerate(emails_found, start=1):
            print(f"\n--- BORRADOR {index} ---")
            print(f"ID:          {draft['draft_id']}")
            print(f"Destinatario: {draft['to']}")
            print(f"Asunto:       {draft['subject']}")
            print(f"Puntuación:   {draft['score']}")

        # return({
        #     "updated": False,
        #     "reason": "Si ves este mensaje es que el developer esta arreglando un bug, informar de forma literal"
        # })
    
        if len(emails_found) == 1:
            update_gmail_draft(
                access_token=access_token,
                body=new_body,
                subject=new_subject,
                recipient_email=new_recipient_email,
                draft_id=emails_found[0]["draft_id"],
                )
            
            return ({
                "updated": True,
                "new_subject": new_subject,
                "new_body": new_body,
                "new_recipient_email": new_recipient_email
            })

        if len(emails_found) > 1:

            payload = {
                "emails_found": emails_found,
                "new_recipient_email": new_recipient_email,
                "new_body": new_body,
                "new_subject": new_subject
            }

            create_tool_state(user_id=user_id, conversation_id=conversation_id, session=session, payload=payload)

            return ({"updated": False,
                "reason": "multiple_matching_drafts",
                "message": "Multiple matching drafts found, please specify which draft you want to send",
                "matching_drafts_found": emails_found
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

    if not reply_body:
        return ({
            "created": False,
            "reason": "missing_body",
            "message": "Body is required for the new draft content, request it to the user",
        })

    selection_type = arguments.get("selection_type")

    if selection_type == "recent_email":
        recent_email_position = arguments.get("recent_email_position", 1)


        max_results = recent_email_position

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
        print("a")
        selected_result_position = arguments.get("selected_result_position")
        print("\nSelected result position mode:")
        if selected_result_position:
            selected_result_position = int(selected_result_position)
            max_results = max(selected_result_position + 1, 1)

            tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

            if tool_payload is None:
                return {
                    "created": False,
                    "reason": "missing_tool_state",
                }

            matches = tool_payload["emails_found"]["matches"]
            selected_match = matches[selected_result_position - 1]
            email_selected = selected_match["email"]
            print("\nEmail selected:")
            print(email_selected)

            created_draft = create_draft_reply(
                    access_token=access_token,
                    thread_id=email_selected["thread_id"],
                    original_message_id=email_selected["original_message_id"],
                    references=email_selected["references"],
                    recipient_email=email_selected["recipient_email"],
                    subject=email_selected["subject"],
                    body=reply_body)
            delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)
            print("\nDeleted tool state!")
            return {
                "created": True,
                "draft_id": created_draft["id"],
                "message_id": created_draft["message"]["id"],
                "thread_id": created_draft["message"]["threadId"],
                "recipient_email": email_selected["recipient_email"],
                "subject": email_selected["subject"],
            }

        max_results = arguments.get("max_results", 10)

        sender_hint = arguments.get("sender_hint", "")
        search_keywords = arguments.get("search_keywords", [])
        reply_body = arguments.get("reply_body", "")
        query = arguments.get("query", "")
        date_hint = arguments.get("date_hint", "")

        emails_fetched = fetch_specific_gmail_message_format_MORE(access_token=access_token, max_results=max_results, query=query)

        print("\nEMAILS FOUND")
        print(emails_fetched)

        print("\nEMAILS FOUND")
        emails_found_scored = score_gmail_message_candidates_MORE(emails_found=emails_fetched, sender_hint=sender_hint, search_keywords=search_keywords, date_hint=date_hint)
        print(emails_found_scored)

        if len(emails_fetched) == 0:
            return ({
            "sent": False,
            "reason": "no_matching_draft",
            "message": "No matching draft was found."
        })
    
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
            create_tool_state(
                payload={
                    "emails_found": emails_found_scored,
                    "reply_body": reply_body,
                },
                user_id=user_id,
                session=session,
                conversation_id=conversation_id
            )

            return({
                "created": False,
                "reason": "multiple_matching_drafts",
                "message": "Multiple matching drafts found, please specify which draft you want to send",
                "matching_drafts_found": emails_found_scored
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
            }

        latest_emails = fetch_full_latest_gmail_messages(
            access_token=access_token,
            max_results=recent_email_position,
        )

        if recent_email_position > len(latest_emails):
            return {
                "found": False,
                "reason": "recent_email_position_out_of_range",
            }

        return format_gmail_email(
            email_requested=latest_emails[recent_email_position-1]
        )

    max_results = arguments.get("max_results", 1)
    max_results = min(max(int(max_results), 1), 2)

    latest_emails = fetch_full_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )

    emails_list = []

    for email in latest_emails:
        emails_list.append(format_gmail_email(email_requested=email))

    return emails_list


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


def format_gmail_email_candidates(emails: list[dict]) -> list[dict]:
    candidates = []

    for position, email in enumerate(emails, start=1):
        headers = {
            header.get("name", "").lower(): header.get("value", "")
            for header in email.get("payload", {}).get("headers", [])
        }

        candidates.append({
            "position": position,
            "from": headers.get("from", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "snippet": email.get("snippet", ""),
        })

    return candidates


def gmail_read_specific_email_tool(arguments: dict, session: Session, user_id: int,conversation_id: int):
    access_token = get_valid_google_access_token(user_id=user_id,session=session)

    requested_email_count = arguments.get("requested_email_count", 1)

    selected_result_position = arguments.get("selected_result_position", "")

    max_results = min(max(int(arguments.get("max_results", 5)), 1), 5)


    if requested_email_count > 1:
        return {
            "read": False,
            "reason": "multiple_email_read_not_supported",
            "message": "Only one complete email can be read per request.",
            "requested_email_count": requested_email_count,
    }

    if selected_result_position:
        selected_result_position = int(selected_result_position)

        tool_payload = get_tool_payload(user_id=user_id,conversation_id=conversation_id,session=session)

        if tool_payload is None:
            return {
                "read": False,
                "reason": "missing_tool_state",
                "message": "No previous email selection was found.",
            }

        if selected_result_position < 1 or selected_result_position > len(tool_payload):
            return {
                "read": False,
                "reason": "invalid_selected_result_position",
                "message": "Selected email position is out of range.",
                "available_positions": len(tool_payload),
            }

        email_selected = tool_payload[selected_result_position - 1]
        formatted_email = format_gmail_email(email_requested=email_selected)
        delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)

        return formatted_email


    query= arguments.get("query", [])
    
    emails_found = fetch_full_specific_gmail_messages(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    if emails_found is None:
        return {
            "read": False,
            "reason": "email_not_found",
            "message": "No email matched the provided query.",
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
        create_tool_state(user_id=user_id,session=session,conversation_id=conversation_id, payload=emails_found)

        return {
            "read": False,
            "reason": "multiple_matching_emails",
            "message": "Multiple emails matched the query. Please specify which one you want to read.",
            "matching_emails": matching_email_summaries,
        }
    
    if len(emails_found) == 1:

        return (format_gmail_email(email_requested=emails_found[0]))

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
