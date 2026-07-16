
from datetime import datetime
from zoneinfo import ZoneInfo

from app.integrations.gmail.client import request_gmail
from app.integrations.gmail.messages import has_real_next_page

GOOGLE_EMAILID_URL = (
    "https://gmail.googleapis.com/gmail/v1/users/me/messages"
)

# -------------- GET SENT EMAIL MESSAGES ---------------

def fetch_sent_gmail_messages_ids(access_token: str, max_results: int,):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "maxResults": max_results,
        "labelIds": "SENT",
    }

    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )

    return response.json()

def fetch_metadata_FSD_sent_gmail_message(access_token: str, message_id: str):

    headers={
        "Authorization": f"Bearer {access_token}",
    }

    params = {
        "format": "metadata",
        "metadataHeaders": ["To", "Subject", "Date"],
    }

    response = request_gmail(
        method="GET",
        url=f"{GOOGLE_EMAILID_URL}/{message_id}",
        headers=headers,
        params=params,
    )
    return response.json()


def format_sent_gmail_message_metadata(message: dict) -> dict:
    headers = message.get("payload", {}).get("headers", [])
    header_values = {
        header.get("name", "").lower(): header.get("value", "")
        for header in headers
    }

    date_iso = ""
    internal_date = message.get("internalDate")

    if internal_date:
        local_datetime = datetime.fromtimestamp(
            int(internal_date) / 1000,
            tz=ZoneInfo("UTC"),
        ).astimezone(ZoneInfo("America/Bogota"))
        date_iso = local_datetime.date().isoformat()

    return {
        "message_id": message.get("id"),
        "thread_id": message.get("threadId"),
        "recipient": header_values.get("to", ""),
        "subject": header_values.get("subject", ""),
        "date": header_values.get("date", ""),
        "date_iso": date_iso,
        "snippet": message.get("snippet", ""),
    }


def fetch_sent_gmail_messages(access_token: str, max_results: int):
    data = fetch_sent_gmail_messages_ids(access_token=access_token, max_results=max_results)

    messages = data.get("messages", [])
    
    sent_message_list = []
    for message in messages:
        fetched_email = fetch_metadata_FSD_sent_gmail_message(access_token=access_token, message_id=message["id"])
        sent_message_list.append(format_sent_gmail_message_metadata(fetched_email))

    has_more = has_real_next_page(
        access_token=access_token,
        next_page_token=data.get("nextPageToken"),
        label_id="SENT",
    )
    return ({
        "emails": sent_message_list,
        "has_more": has_more,
        "returned_count": len(sent_message_list)
    })



# -------------- SEARCH SENT EMAIL MESSAGES ---------------

def fetch_specific_sent_gmail_messages_ids(access_token: str, max_results: int,query: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "q": query,
        "maxResults": max_results,
        "labelIds": "SENT",
    }

    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )

    return response.json()


def fetch_specific_sent_gmail_messages(access_token: str, max_results: int, query: str):
    data = fetch_specific_sent_gmail_messages_ids(access_token=access_token, max_results=max_results, query=query)

    messages = data.get("messages", [])
    
    sent_message_list = []
    for message in messages:
        fetched_email = fetch_metadata_FSD_sent_gmail_message(access_token=access_token, message_id=message["id"])
        sent_message_list.append(format_sent_gmail_message_metadata(fetched_email))

    has_more = has_real_next_page(
        access_token=access_token,
        query=query,
        label_id="SENT",
        next_page_token=data.get("nextPageToken"),
    )

    return {
        "emails": sent_message_list,
        "has_more": has_more,
        "returned_count": len(sent_message_list),
    }

