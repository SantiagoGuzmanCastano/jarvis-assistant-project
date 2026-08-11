
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial
from zoneinfo import ZoneInfo

from app.integrations.gmail.client import request_gmail
from app.integrations.gmail.content import format_full_gmail_message
from app.integrations.gmail.drafts import normalize_text
from app.integrations.gmail.messages import (
    fetch_full_specific_gmail_messages_metadata,
    has_real_next_page,
)
from app.integrations.gmail.search import (
    build_gmail_keyword_fallback_query,
)

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
        "returned_count": len(sent_message_list),
        "next_page_token": data.get("nextPageToken") if has_more else None,
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


GMAIL_SENT_FALLBACK_SCAN_LIMIT = 50
GMAIL_SENT_FALLBACK_WORKERS = 5


def _sent_message_matches_keywords(
    message: dict,
    search_keywords: list[str],
) -> bool:
    content = format_full_gmail_message(message)
    searchable_text = normalize_text(
        " ".join(
            [
                content.get("recipient", ""),
                content.get("subject", ""),
                message.get("snippet", ""),
                content.get("body", ""),
            ]
        )
    )
    normalized_keywords = [
        normalize_text(keyword)
        for keyword in search_keywords
        if normalize_text(keyword)
    ]
    return any(keyword in searchable_text for keyword in normalized_keywords)


def _fetch_fallback_sent_messages(
    *,
    access_token: str,
    max_results: int,
    query: str,
    search_keywords: list[str],
) -> tuple[list[dict], bool] | None:
    fallback_query = build_gmail_keyword_fallback_query(
        query=query,
        search_keywords=search_keywords,
    )
    if fallback_query is None:
        return None

    fallback_data = fetch_specific_sent_gmail_messages_ids(
        access_token=access_token,
        max_results=max(max_results, GMAIL_SENT_FALLBACK_SCAN_LIMIT),
        query=fallback_query,
    )
    message_ids = [
        message["id"]
        for message in fallback_data.get("messages", [])
    ]
    fetch_full_message = partial(
        fetch_full_specific_gmail_messages_metadata,
        access_token=access_token,
    )
    with ThreadPoolExecutor(
        max_workers=min(GMAIL_SENT_FALLBACK_WORKERS, len(message_ids) or 1)
    ) as executor:
        fetched_messages = list(
            executor.map(fetch_full_message, message_ids)
        )

    matching_messages = [
        message
        for message in fetched_messages
        if _sent_message_matches_keywords(message, search_keywords)
    ]
    has_more = (
        len(matching_messages) > max_results
        or bool(fallback_data.get("nextPageToken"))
    )
    return matching_messages[:max_results], has_more


def fetch_specific_sent_gmail_messages(
    access_token: str,
    max_results: int,
    query: str,
    search_keywords: list[str] | None = None,
):
    data = fetch_specific_sent_gmail_messages_ids(access_token=access_token, max_results=max_results, query=query)

    messages = data.get("messages", [])
    used_fallback = False
    fallback_has_more = False
    if not messages and search_keywords:
        fallback_result = _fetch_fallback_sent_messages(
            access_token=access_token,
            max_results=max_results,
            query=query,
            search_keywords=search_keywords,
        )
        if fallback_result is not None:
            messages, fallback_has_more = fallback_result
            used_fallback = True
    
    sent_message_list = []
    for message in messages:
        fetched_email = (
            message
            if used_fallback
            else fetch_metadata_FSD_sent_gmail_message(
                access_token=access_token,
                message_id=message["id"],
            )
        )
        sent_message_list.append(format_sent_gmail_message_metadata(fetched_email))

    has_more = (
        fallback_has_more
        if used_fallback
        else has_real_next_page(
            access_token=access_token,
            query=query,
            label_id="SENT",
            next_page_token=data.get("nextPageToken"),
        )
    )

    return {
        "emails": sent_message_list,
        "has_more": has_more,
        "returned_count": len(sent_message_list),
        "next_page_token": (
            data.get("nextPageToken")
            if has_more and not used_fallback
            else None
        ),
    }

