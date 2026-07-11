

import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from email.message import EmailMessage
import unicodedata
from zoneinfo import ZoneInfo

import requests


GOOGLE_CREATEDRAFT_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"

# --------------CREATE DRAFT---------------

def create_gmail_draft(access_token:str, body:str, subject:str, recipient_email:str):

    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message= EmailMessage()
    message.set_content(body)
    message["To"] = recipient_email
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload = {
        "message": {
        "raw": encoded_message,
        }
    }

    response = requests.post(GOOGLE_CREATEDRAFT_URL,headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


# --------------FETCH DRAFTS---------------

GOOGLE_DRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"


def fetch_gmail_drafts_ids(
    access_token: str,
    max_results: int,
    query: str | None = None,
    page_token: str | None = None,
):
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params: dict[str, str | int] = {
        "maxResults": max_results,
    }

    if query:
        params["q"] = query

    if page_token:
        params["pageToken"] = page_token

    response = requests.get(GOOGLE_DRAFTS_URL, headers=headers, params=params)
    response.raise_for_status()

    return response.json()

#RESPUESTA ESPERADA
#{
#   "drafts": [
#     {
#       "id": "r123456789",
#       "message": {
#         "id": "18fabc1234567890",
#         "threadId": "18fabc9999999999"
#       }
#     }
#   ],
#   "resultSizeEstimate": 1
# }


def fetch_gmail_draft_metadata(draft_id: str, access_token: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "format": "metadata",
        "metadataHeaders": ["To","From", "Subject", "Date"],
    }

    response = requests.get(f"{GOOGLE_DRAFTS_URL}/{draft_id}", headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def fetch_gmail_draft_full(draft_id: str, access_token: str):
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "format": "full",
    }

    response = requests.get(
        f"{GOOGLE_DRAFTS_URL}/{draft_id}",
        headers=headers,
        params=params,
    )
    response.raise_for_status()
    return response.json()


def format_gmail_draft_candidate(draft: dict, position: int) -> dict:
    message = draft.get("message", {})
    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in message.get("payload", {}).get("headers", [])
    }

    date_value = headers.get("date", "")
    internal_date = message.get("internalDate")
    utc_timezone = ZoneInfo("UTC")
    user_timezone = ZoneInfo("America/Bogota")

    if internal_date:
        try:
            date_value = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=utc_timezone,
            ).astimezone(user_timezone).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    elif date_value:
        try:
            parsed_date = parsedate_to_datetime(date_value)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=utc_timezone)
            date_value = parsed_date.astimezone(user_timezone).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass

    return {
        "position": position,
        "draft_id": draft.get("id"),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": date_value,
        "snippet": message.get("snippet", ""),
    }

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

def format_gmail_draft_full(draft: dict, position: int) -> dict:
    message = draft.get("message", {})

    headers = {
        header.get("name", "").lower(): header.get("value", "")
        for header in message.get("payload", {}).get("headers", [])
    }

    date_value = headers.get("date", "")
    internal_date = message.get("internalDate")
    utc_timezone = ZoneInfo("UTC")
    user_timezone = ZoneInfo("America/Bogota")

    if internal_date:
        try:
            date_value = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=utc_timezone,
            ).astimezone(user_timezone).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    elif date_value:
        try:
            parsed_date = parsedate_to_datetime(date_value)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=utc_timezone)
            date_value = parsed_date.astimezone(user_timezone).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass

    body_data = find_text_body(message.get("payload", {}))

    if body_data:
        padded_body = body_data + "=" * (-len(body_data) % 4)
        decoded_body = base64.urlsafe_b64decode(padded_body)
        body = decoded_body.decode("utf-8", errors="replace")
    else:
        body = message.get("snippet", "")

    return {
        "position": position,
        "draft_id": draft.get("id"),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": date_value,
        "snippet": message.get("snippet", ""),
        "body": body,
    }

def has_real_next_draft_page(
    access_token: str,
    query: str,
    next_page_token: str | None,
) -> bool:
    if not next_page_token:
        return False

    next_page = fetch_gmail_drafts_ids(
        access_token=access_token,
        max_results=1,
        query=query,
        page_token=next_page_token,
    )

    return bool(next_page.get("drafts"))


def fetch_specific_gmail_drafts(access_token: str,max_results: int,query: str,) -> dict:
    data = fetch_gmail_drafts_ids(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    drafts = []
    for position, draft in enumerate(data.get("drafts", []), start=1):
        fetched_draft = fetch_gmail_draft_metadata(
            access_token=access_token,
            draft_id=draft["id"],
        )
        drafts.append(
            format_gmail_draft_candidate(
                draft=fetched_draft,
                position=position,
            )
        )

    has_more = has_real_next_draft_page(
        access_token=access_token,
        query=query,
        next_page_token=data.get("nextPageToken"),
    )

    return {
        "drafts": drafts,
        "returned_count": len(drafts),
        "has_more": has_more,
    }


def fetch_specific_gmail_drafts_full(access_token: str,max_results: int,query: str,) -> dict:
    data = fetch_gmail_drafts_ids(
        access_token=access_token,
        max_results=max_results,
        query=query,
    )

    drafts = []
    for position, draft in enumerate(data.get("drafts", []), start=1):
        fetched_draft = fetch_gmail_draft_full(
            access_token=access_token,
            draft_id=draft["id"],
        )
        drafts.append(
            format_gmail_draft_full(
                draft=fetched_draft,
                position=position,
            )
        )

    has_more = has_real_next_draft_page(
        access_token=access_token,
        query=query,
        next_page_token=data.get("nextPageToken"),
    )

    #esto se guarda en el payload de update_email?draft_tool
    return {
        "drafts": drafts,
        "returned_count": len(drafts),
        "has_more": has_more,
    }









def fetch_gmail_drafts(access_token: str, max_results: int):
    fetched_draft = fetch_gmail_drafts_ids(access_token=access_token, max_results=max_results)

    draft_list = []
    for draft in fetched_draft.get("drafts", []):
        fetched_draft_email = fetch_gmail_draft_metadata(access_token=access_token, draft_id=draft["id"])
        draft_list.append(fetched_draft_email)

    counter = 0
    for index, draft in enumerate(draft_list):
        message = draft.get("message", {})
        headers = message.get("payload", {}).get("headers", [])

        header_values = {}

        for header in headers:
            name = header.get("name", "").lower()
            header_values[name] = header.get("value", "")

        print(f"""
        ---------------- DRAFT {index} ----------------
        Draft ID: {draft.get("id")}
        To: {header_values.get("to")}
        Subject: {header_values.get("subject")}
        Date: {header_values.get("date")}
        Snippet: {message.get("snippet")}
        -------------------------------------------
        """)
        counter +=1
    return draft_list

# [
#   {
#     "id": "r123456789",
#     "message": {
#       "id": "18fabc1234567890",
#       "threadId": "18fabc9999999999",
#       "labelIds": ["DRAFT"],
#       "snippet": "Hola Pedro, te escribo para confirmar la reunión de mañana...",
#       "payload": {
#         "headers": [
#           {
#             "name": "To",
#             "value": "pedro@example.com"
#           },
#           {
#             "name": "Subject",
#             "value": "Reunión de mañana"
#           },
#           {
#             "name": "Date",
#             "value": "Fri, 19 Jun 2026 10:30:00 -0500"
#           }
#         ]
#       }
#     }
#   },
#   {
#     "id": "r987654321",
#     "message": {
#       "id": "18fabc9876543210",
#       "threadId": "18fabc8888888888",
#       "labelIds": ["DRAFT"],
#       "snippet": "Hola María, te envío el resumen del proyecto Jarvis...",
#       "payload": {
#         "headers": [
#           {
#             "name": "To",
#             "value": "maria@example.com"
#           },
#           {
#             "name": "Subject",
#             "value": "Resumen del proyecto"
#           },
#           {
#             "name": "Date",
#             "value": "Fri, 19 Jun 2026 11:15:00 -0500"
#           }
#         ]
#       }
#     }
#   }
# ]

# --------------SEND DRAFT---------------

GOOGLE_SEND_DRAFT_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts/send"


def send_gmail_draft(draft_id:str, access_token: str):


    headers={
        "Authorization": f"Bearer {access_token}",
    }

    payload = {
        "id":draft_id
    }

    response = requests.post(
    GOOGLE_SEND_DRAFT_URL,
    headers=headers,
    json=payload)
    response.raise_for_status()
    return response.json()

# --------------SEARCH DRAFT---------------


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""

    text = text.lower().strip()

    normalized_text = unicodedata.normalize("NFD", text)

    text_without_accents = ""

    for character in normalized_text:
        if unicodedata.category(character) != "Mn":
            text_without_accents += character

    return text_without_accents

# --------------UPDATE DRAFT---------------


GOOGLE_UPDATEDRAFTS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"


def update_gmail_draft(access_token: str, body: str, subject: str, recipient_email: str, draft_id: int):

    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message= EmailMessage()
    message.set_content(body)
    message["To"] = recipient_email
    message["Subject"] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload = {
        "message": {
        "raw": encoded_message,
        }
    }

    response = requests.put(f"{GOOGLE_UPDATEDRAFTS_URL}/{draft_id}",headers=headers,json=payload)
    response.raise_for_status()
    return response.json()


# --------------CREATE DRAFT REPLY MESSAGES---------------

GOOGLE_CREATEDRAFTREPLY_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"


def create_draft_reply(access_token:str, thread_id: str, original_message_id: str, references: str, recipient_email: str, subject: str, body: str):

    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    message= EmailMessage()
    message.set_content(body)
    message["To"] = recipient_email
    message["Subject"] = subject
    message["In-Reply-To"] = original_message_id
    message["References"] = references

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload = {
        "message": {
        "raw": encoded_message,
        "threadId": thread_id
        }
    }

    response = requests.post(f"{GOOGLE_CREATEDRAFTREPLY_URL}",headers=headers,json=payload)
    response.raise_for_status()
    return response.json()
