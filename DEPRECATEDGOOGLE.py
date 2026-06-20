

import base64
from email.message import EmailMessage

import requests

# --------------UNREAD---------------

GOOGLE_EMAILID_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'


def fetch_unread_gmail_messages_ids(access_token: str, max_results: int):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    query = "category:primary is:unread"

    params={
        "q": query,
        "maxResults": max_results,
    }
    #q significa query de búsqueda, igual que cuando escribes en la barra de búsqueda de Gmail.
    #is:unread significa: solo correos no leídos.

    response = requests.get(GOOGLE_EMAILID_URL, headers=headers,params=params)

    print("ACCESS TOKEN START:", access_token[:20])
    print("GMAIL STATUS:", response.status_code)
    print("GMAIL ERROR:", response.text)
    response.raise_for_status()

    return response.json()

# {
#   "messages": [
#     {
#       "id": "18fabc1234567890",
#       "threadId": "18fabc1234567890"
#     },
#     {
#       "id": "18fabc9876543210",
#       "threadId": "18fabc9876543210"
#     }
#   ],
#   "resultSizeEstimate": 2
# }

    #https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread&maxResults=5


GOOGLE_MESSAGES_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'


def fetch_gmail_message_metadata(message_id: str, access_token: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "format": "metadata",
        "metadataHeaders": ["From", "Subject", "Date"],
    }

    response = requests.get(
        f"{GOOGLE_MESSAGES_URL}/{message_id}", headers=headers,params=params)
    
    response.raise_for_status()
    return response.json()

    # {
    #   "id": "18fabc1234567890",
    #   "threadId": "18fabc9999999999",
    #   "snippet": "Hola, te escribo para confirmar...",
    #   "payload": {
    #     "headers": [
    #       { "name": "From", "value": "Juan Pérez <juan@example.com>" },
    #       { "name": "Subject", "value": "Reunión de mañana" },
    #       { "name": "Date", "value": "Thu, 18 Jun 2026 09:30:00 -0500" }
    #     ]
    #   }
    # }

    
def fetch_unread_gmail_messages(access_token:str, max_results: int):
    data = fetch_unread_gmail_messages_ids(access_token=access_token, max_results=max_results)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_gmail_message_metadata(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)

    return message_list

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



# --------------LATEST---------------



def fetch_latest_gmail_messages_ids(access_token: str, max_results: int):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    query = "category:primary"

    params={
        "q": query,
        "maxResults": max_results,
    }
    #q significa query de búsqueda, igual que cuando escribes en la barra de búsqueda de Gmail.
    #is:unread significa: solo correos no leídos.

    response = requests.get(GOOGLE_EMAILID_URL, headers=headers,params=params)

    print("ACCESS TOKEN START:", access_token[:20])
    print("GMAIL STATUS:", response.status_code)
    print("GMAIL ERROR:", response.text)
    response.raise_for_status()

    return response.json()


def fetch_latest_gmail_messages(access_token:str, max_results: int):
    data = fetch_latest_gmail_messages_ids(access_token=access_token, max_results=max_results)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_gmail_message_metadata(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)

    return message_list




# --------------SEND---------------


GOOGLE_SENDEMAIL_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

def gmail_send_email_message(access_token: str, recipient_email: str, subject: str, body:str ):

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
        "raw": encoded_message,
    }

    response = requests.post(GOOGLE_SENDEMAIL_URL,headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# --------------SEARCH---------------


def fetch_specific_gmail_messages_id(access_token: str, max_results: int, query: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "q": query,
        "maxResults": max_results,
    }
    #q significa query de búsqueda, igual que cuando escribes en la barra de búsqueda de Gmail.
    #is:unread significa: solo correos no leídos.

    response = requests.get(GOOGLE_EMAILID_URL, headers=headers,params=params)

    print("ACCESS TOKEN START:", access_token[:20])
    print("GMAIL STATUS:", response.status_code)
    print("GMAIL ERROR:", response.text)
    response.raise_for_status()

    return response.json()

def fetch_specific_gmail_message(access_token:str, max_results: int, query: str):
    data = fetch_specific_gmail_messages_id(access_token=access_token, max_results=max_results, query=query)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_gmail_message_metadata(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)

    return message_list