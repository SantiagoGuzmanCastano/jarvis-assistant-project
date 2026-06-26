from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import create_gmail_draft, fetch_gmail_drafts, search_gmail_drafts, send_gmail_draft
from app.integrations.gmail.messages import fetch_latest_gmail_messages, fetch_specific_gmail_message, fetch_unread_gmail_messages
from app.integrations.gmail.send import gmail_send_email_message
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

def read_unread_emails_tool(arguments: dict, user_id: int, session: Session):

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

# --------------GET LATEST---------------

def read_latest_emails_tool(arguments: dict, user_id: int, session: Session):

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


# --------------SEND---------------

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


# --------------SEARCH---------------

def gmail_search_email_message_tool(arguments: dict, user_id: int, session: Session):
    
    query = arguments['query']
    max_results = arguments["max_results"]
    
    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    email_searched = fetch_specific_gmail_message(access_token=access_token, query=query, max_results=max_results)
    return email_searched


# --------------DRAFT---------------

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
    
    response = search_gmail_drafts(access_token=access_token, max_results=max_results, recipient_hint=recipient_hint, subject_keywords=subject_keywords, snippet_keywords=snippet_keywords)


    print('\nDRAFT MATCHES FOUND:')
    print(response)

    if response is None:
        raise ValueError("Draft search failed")
    
    if len(response) == 0:
        return ({
            "sent": False,
            "reason": "no_matching_draft",
            "message": "No matching draft was found."
        })
    
    if len(response) > 1:

        for item in response:
            for key, value in item.items():
                print(key, value, type(value))
            print("-----------------------------")
        create_tool_state(user_id=user_id, conversation_id=conversation_id, payload=response, session=session)

        return ({
            "sent": False,
            "reason": "multiple_matching_drafts",
            "message": "Multiple matching drafts found, please specify which draft you want to send",
            "matching_drafts_found": response
        })
        
    selected_draft = response[0]
    send_gmail_draft(draft_id=selected_draft["draft_id"], access_token=access_token)
    return ({
        "sent": True,
        "draft_id":selected_draft["draft_id"],
        "selected_draft": selected_draft,
        })
