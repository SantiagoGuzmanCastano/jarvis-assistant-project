from sqlalchemy.orm import Session

from app.integrations.gmail.drafts import create_gmail_draft, fetch_gmail_drafts, search_gmail_drafts, send_gmail_draft
from app.integrations.gmail.messages import fetch_latest_gmail_messages, fetch_specific_gmail_message, fetch_unread_gmail_messages
from app.integrations.gmail.send import gmail_send_email_message
from app.services.external_auth_service import get_valid_google_access_token


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


# --------------SEND---------------

def gmail_send_email_message_tool(arguments: dict, user_id: int, session: Session):
    
    recipient_email = arguments.get("recipient_email")
    subject = arguments.get("subject")
    body = arguments.get("body")


    access_token=get_valid_google_access_token(user_id=user_id, session=session)
    email_sent = gmail_send_email_message(
        access_token=access_token,
        recipient_email=recipient_email,
        subject=subject,
        body=body,
    )
    
    return email_sent


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

    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    new_draft_message = create_gmail_draft(access_token=access_token, body=body, subject=subject, recipient_email=recipient_email)
    return new_draft_message


def gmail_get_drafted_emails_tool(arguments: dict,user_id: int, session: Session):

    max_results = arguments.get("max_results", 3)
    max_results = min(max(int(max_results), 1), 5)
    access_token = get_valid_google_access_token(user_id=user_id, session=session)
    draft_email = fetch_gmail_drafts(acces_token=access_token,max_results=max_results)
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


def gmail_send_drafted_email_tool(arguments:dict, user_id: int, session: Session):
    
    recipient_hint = arguments.get("recipient_hint","")
    subject_keywords = arguments.get("subject_keywords",[])
    snippet_keywords = arguments.get("snippet_keywords",[])
    max_results = arguments.get("max_results",10)

    access_token = get_valid_google_access_token(user_id=user_id, session=session)

    response = search_gmail_drafts(access_token=access_token, max_results=max_results, recipient_hint=recipient_hint, subject_keywords=subject_keywords, snippet_keywords=snippet_keywords)

    draft_id = response[0]["draft_id"]

    sent_draft = send_gmail_draft(draft_id=draft_id, access_token=access_token)
    return sent_draft