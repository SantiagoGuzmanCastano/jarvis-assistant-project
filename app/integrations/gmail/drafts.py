

import base64
from email.message import EmailMessage
import unicodedata

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


def fetch_gmail_drafts_ids(access_token:str, max_results:int):
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "maxResults": max_results,
    }
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


def fetch_gmail_draft_metadata(draft_id: int, access_token: str):

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


def search_gmail_drafts(access_token: str,max_results: int, recipient_hint: str, subject_keywords: list[str], snippet_keywords:list[str]):

    drafted_emails=fetch_gmail_drafts(access_token=access_token, max_results=max_results)

    #EL QUE RECIBE EL EMAIL
    recipient_hint = normalize_text(recipient_hint)

    normalized_subject_keywords = []
    for word in subject_keywords:
        normalized_subject_keywords.append(normalize_text(word))

    normalized_snippet_keywords = []
    for word in snippet_keywords:
        normalized_snippet_keywords.append(normalize_text(word))

    matches = []
    for draft in drafted_emails:

        #caso que no existan
        to = ""
        subject = ""

        score = 0

        draft_id = draft["id"]
        # snippet = draft['message']['snippet']

        to_original = ""
        snippet_original = ""
        subject_original = ""

        snippet = normalize_text(draft["message"].get("snippet", ""))
        snippet_original = draft["message"].get("snippet", "")

        for header in draft["message"]["payload"]['headers']:
            if header['name'] == "To":
                to = normalize_text(header['value'])
                to_original = header["value"]
            elif header['name'] == "Subject":
                subject = normalize_text(header['value'])
                subject_original = header["value"]
        
        if recipient_hint and recipient_hint in to:
            score +=3

        for word in normalized_subject_keywords:
            if word in subject:
                score +=3

        for word in normalized_snippet_keywords:
            if word in snippet:
                score +=1

        if score > 0:
            matches.append({
            "draft_id":draft_id,
            "to": to_original,
            "subject": subject_original,
            "snippet": snippet_original,
            "score": score
            })

    matches.sort(key=lambda match: match["score"], reverse=True)
    return matches


def search_gmail_drafts_no_snippet(access_token: str,max_results: int, recipient_hint: str, subject_keywords: list[str]):

    drafted_emails=fetch_gmail_drafts(access_token=access_token, max_results=max_results)

    #EL QUE RECIBE EL EMAIL
    recipient_hint = normalize_text(recipient_hint)

    normalized_subject_keywords = []
    for word in subject_keywords:
        normalized_subject_keywords.append(normalize_text(word))

    matches = []
    for draft in drafted_emails:

        #caso que no existan
        to = ""
        subject = ""

        score = 0

        draft_id = draft["id"]
        # snippet = draft['message']['snippet']

        to_original = ""
        subject_original = ""


        for header in draft["message"]["payload"]['headers']:
            if header['name'] == "To":
                to = normalize_text(header['value'])
                to_original = header["value"]
            elif header['name'] == "Subject":
                subject = normalize_text(header['value'])
                subject_original = header["value"]
        
        if recipient_hint and recipient_hint in to:
            score +=3

        for word in normalized_subject_keywords:
            if word in subject:
                score +=3

        if score > 0:
            matches.append({
            "draft_id":draft_id,
            "to": to_original,
            "subject": subject_original,
            "score": score
            })

    matches.sort(key=lambda match: match["score"], reverse=True)
    return matches

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
