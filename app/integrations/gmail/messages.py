

from datetime import date, datetime, time, timedelta
from email.utils import parseaddr, parsedate_to_datetime
from zoneinfo import ZoneInfo

from app.integrations.gmail.client import request_gmail
from app.integrations.gmail.drafts import normalize_text

def build_gmail_search_query(sender_hint: str, search_keywords: list[str], date_hint: str | None,) -> str:
    query_parts = []

    if sender_hint:
        if "@" in sender_hint:
            query_parts.append(f"from:{sender_hint}")
        else:
            sender_words = sender_hint.split()
            if sender_words:
                query_parts.append(f"({' OR '.join(sender_words)})")

    if search_keywords:
        query_parts.append(f"({' OR '.join(search_keywords)})")

    if date_hint:
        query_parts.append(date_hint)

    return " ".join(query_parts)

#---------------FETCH IDS---------------
# region fetch ids


def fetch_unread_gmail_messages_ids(access_token: str, max_results: int, query: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    print("\nQuery")
    print(query)

    params={
        "q": query,
        
        "maxResults": max_results,
    }

    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )

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


def fetch_latest_gmail_messages_ids(access_token: str, max_results: int):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "q": LATEST_EMAILS_QUERY,
        "maxResults": max_results,
    }


    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )

    return response.json()


def fetch_specific_gmail_messages_id(access_token: str, max_results: int, query: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }


    params = {
        "q": query,
        "labelIds": ["INBOX"],
        "maxResults": max_results,
    }

    print("\nquery used:")
    print(query)

    #q significa query de búsqueda, igual que cuando escribes en la barra de búsqueda de Gmail.
    #is:unread significa: solo correos no leídos.

    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )
    # print("\nQUERY:", repr(query))
    # print("URL:", response.url)
    # print("RESPONSE:", response.json())

    return response.json()

# {
#   "messages": [
#     {
#       "id": "18fabc1234567890",
#       "threadId": "18fabc9999999999"
#     },
#     {
#       "id": "18fabc9876543210",
#       "threadId": "18fabc8888888888"
#     }
#   ],
#   "resultSizeEstimate": 2
# }


# endregion

# --------------UNREAD---------------
# region unread
GOOGLE_EMAILID_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'


GOOGLE_MESSAGES_URL = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'

LATEST_EMAILS_QUERY = "category:primary"


def move_gmail_message_to_trash(access_token: str, message_id: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = request_gmail(
        method="POST",
        url=f"{GOOGLE_MESSAGES_URL}/{message_id}/trash",
        headers=headers,
    )
    return response.json()


def fetch_metadata_FSD_gmail_message(message_id: str, access_token: str):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "format": "metadata",
        "metadataHeaders": ["From", "Subject", "Date"],
    }

    response = request_gmail(
        method="GET",
        url=f"{GOOGLE_MESSAGES_URL}/{message_id}",
        headers=headers,
        params=params,
    )
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

    
def fetch_unread_gmail_messages(access_token:str, max_results: int, query: str):
    data = fetch_unread_gmail_messages_ids(access_token=access_token, max_results=max_results, query = query)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_metadata_FSD_gmail_message(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)

    has_more = has_real_next_page(access_token=access_token, query=query, next_page_token=data.get("nextPageToken"))
    return ({
        "emails": message_list,
        "has_more": has_more,
        "returned_count": len(message_list),
        "next_page_token": data.get("nextPageToken") if has_more else None,
    })

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
    # ]

# endregion

# --------------LATEST---------------
# region latest

def fetch_latest_gmail_messages(access_token:str, max_results: int):
    data = fetch_latest_gmail_messages_ids(access_token=access_token, max_results=max_results)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_metadata_FSD_gmail_message(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)

    has_more = has_real_next_page(
        access_token=access_token,
        next_page_token=data.get("nextPageToken"),
        query=LATEST_EMAILS_QUERY,
    )

    return {
        "emails": message_list,
        "has_more": has_more,
        "returned_count": len(message_list),
        "next_page_token": data.get("nextPageToken") if has_more else None,
    }

# endregion

# --------------SEARCH---------------
# region search

def fetch_specific_gmail_message_format_FSD(access_token:str, max_results: int, query: str):
    data = fetch_specific_gmail_messages_id(access_token=access_token, max_results=max_results, query=query)

    print("")
    print(data)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_metadata_FSD_gmail_message(message_id=message["id"], access_token=access_token)

        message_headers = fetched_email["payload"]["headers"]
        sender = ""
        subject = ""
        date = ""
        normalized_date = ""

        for header in message_headers:
            header_name = header.get("name", "").lower()
            header_value = header.get("value", "")

            if header_name == "from":
                sender = header_value
            elif header_name == "subject":
                subject = header_value
            elif header_name == "date":
                date = header_value

        if date:
            try:
                parsed_date = parsedate_to_datetime(date)
                normalized_date = parsed_date.astimezone(
                    ZoneInfo("America/Bogota")
                ).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                normalized_date = ""
                

        message_list.append({
            "message_id": fetched_email["id"],
            "thread_id": fetched_email["threadId"],
            "sender": sender,
            "subject": subject,
            "date": date,
            "date_iso": normalized_date,
            "snippet": fetched_email.get("snippet", ""),
        })

    has_more = has_real_next_page(access_token=access_token, query=query, next_page_token=data.get("nextPageToken"))
    return ({
        "emails": message_list,
        "has_more": has_more,
        "returned_count": len(message_list),
        "next_page_token": data.get("nextPageToken") if has_more else None,
    })

# [
#   
#   {
#     "id": "18fabc1234567890",
#     "threadId": "18fabc9999999999",
#     "snippet": "Hola, te escribo para confirmar...",
#     "payload": {
#       "headers": [
#         { "name": "From", "value": "Nelson <nelson@example.com>" },
#         { "name": "Subject", "value": "Prórroga de contrato" },
#         { "name": "Date", "value": "Thu, 18 Jun 2026 08:00:00 -0500" }
#       ]
#     }
#   }
# ]



# endregion

# --------------READ EMAIL MESSAGES---------------
# region read
# 
def fetch_full_latest_gmail_messages(access_token: str, max_results: int):

    message_page = fetch_latest_gmail_messages(
        access_token=access_token,
        max_results=max_results,
    )


    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "format": "full",
        "maxResults": max_results
    }

    latest_emails = []

    for message in message_page["emails"]:
        message_id = message["id"]

        response = request_gmail(
            method="GET",
            url=f"{GOOGLE_MESSAGES_URL}/{message_id}",
            headers=headers,
            params=params,
        )

        latest_emails.append(response.json())

    return latest_emails

def fetch_full_specific_gmail_messages_metadata(access_token: str, message_id: int):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params={
        "format":"full"
    }
    #q significa query de búsqueda, igual que cuando escribes en la barra de búsqueda de Gmail.
    #is:unread significa: solo correos no leídos.

    response = request_gmail(
        method="GET",
        url=f"{GOOGLE_MESSAGES_URL}/{message_id}",
        headers=headers,
        params=params,
    )
    return response.json()


def fetch_full_specific_gmail_messages(access_token: str, max_results: int, query: str):
    data = fetch_specific_gmail_messages_id(access_token=access_token, max_results=max_results, query=query)

    if not data.get("messages",[]):
        return None

    message_list = []
    for message in data.get("messages",[]):
        message_id = message["id"]
        full_email = fetch_full_specific_gmail_messages_metadata(access_token=access_token, message_id=message_id)
        message_list.append(full_email)

    
    return message_list

# endregion

# --------------FOR CREATE DRAFT REPLY: ---------------
# region create draft reply

def fetch_metadata_MORE_gmail_message(access_token: str, message_id: int):

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
    "format": "metadata",
    "metadataHeaders": [
        "From",
        "Reply-To",
        "Subject",
        "Date",
        "Message-ID",
        "References",
        ],
    }

    response = request_gmail(
        method="GET",
        url=f"{GOOGLE_MESSAGES_URL}/{message_id}",
        headers=headers,
        params=params,
    )
    return response.json()


# {
#   "id": "19efb59f8a1e7535",
#   "threadId": "19efb404e41cf513",
#   "labelIds": ["UNREAD", "INBOX"],
#   "snippet": "Hola, quería confirmar la reunión...",
#   "payload": {
#     "mimeType": "text/plain",
#     "headers": [
#       {
#         "name": "From",
#         "value": "Pedro <pedro@example.com>"
#       },
#       {
#         "name": "Reply-To",
#         "value": "pedro@example.com"
#       },
#       {
#         "name": "Subject",
#         "value": "Reunión de mañana"
#       },
#       {
#         "name": "Message-Id",
#         "value": "<abc123@mail.gmail.com>"
#       },
#       {
#         "name": "References",
#         "value": "<previous-message@mail.gmail.com>"
#       }
#     ]
#   },
#   "internalDate": "1782333438000"
# }


def search_latest_gmail_messages_for_metadata(access_token:str, max_results: int):
    data = fetch_latest_gmail_messages_ids(access_token=access_token, max_results=max_results)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_metadata_MORE_gmail_message(message_id=message["id"], access_token=access_token)
        message_list.append(fetched_email)
    return message_list



#################### SPECIFIC ########################

def fetch_specific_gmail_message_format_MORE(access_token:str, max_results: int, query: str):
    data = fetch_specific_gmail_messages_id(access_token=access_token, max_results=max_results, query= query)

    message_list = []
    for message in data.get("messages",[]):
        fetched_email = fetch_metadata_MORE_gmail_message(message_id=message["id"], access_token=access_token)
        
        from_email = ""
        reply_to_email = ""
        subject = ""
        references = ""
        original_message_id = ""
        date = ""
        date_iso = ""
        sender = ""

        headers = fetched_email.get("payload", {}).get("headers", [])

        for header in headers:
            header_name = header.get("name", "").lower()
            header_value = header.get("value", "")

            if header_name == "from":
                sender = header_value
                _, from_email = parseaddr(header_value)
            elif header_name == "reply-to":
                _, reply_to_email = parseaddr(header_value)
            elif header_name == "subject":
                subject = header_value
            elif header_name == "message-id":
                original_message_id = header_value
            elif header_name == "references":
                references = header_value
            elif header_name == "date":
                date = header_value

        if date:
            try:
                parsed_date = parsedate_to_datetime(date)
                date_iso = parsed_date.astimezone(
                    ZoneInfo("America/Bogota")
                ).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                date_iso = ""

        recipient_email = reply_to_email or from_email
        references = f"{references} {original_message_id}".strip()

        message_list.append({
            "thread_id": fetched_email["threadId"],
            "sender": sender,
            "original_message_id": original_message_id,
            "references": references,
            "recipient_email": recipient_email,
            "subject": subject,
            "date": date,
            "date_iso": date_iso,
            "snippet": fetched_email.get("snippet", ""),
        })

    has_more = has_real_next_page(
        access_token=access_token,
        query=query,
        next_page_token=data.get("nextPageToken"),
    )

    return {
        "emails": message_list,
        "returned_count": len(message_list),
        "has_more": has_more,
    }


# {
#   "id": "19efb59f8a1e7535",
#   "threadId": "19efb404e41cf513",
#   "labelIds": ["UNREAD", "INBOX"],
#   "snippet": "Hola, quería confirmar la reunión...",
#   "payload": {
#     "mimeType": "text/plain",
#     "headers": [
#       {
#         "name": "From",
#         "value": "Pedro <pedro@example.com>"
#       },
#       {
#         "name": "Reply-To",
#         "value": "pedro@example.com"
#       },
#       {
#         "name": "Subject",
#         "value": "Reunión de mañana"
#       },
#       {
#         "name": "Message-Id",
#         "value": "<abc123@mail.gmail.com>"
#       },
#       {
#         "name": "References",
#         "value": "<previous-message@mail.gmail.com>"
#       }
#     ]
#   },
#   "internalDate": "1782333438000"
# }

# endregion





def score_gmail_message_candidates(emails_found: list, sender_hint: str, search_keywords: list, date_hint):
    
    sender_hint = normalize_text(sender_hint)
    search_keywords = [
        normalize_text(word)
        for word in search_keywords
    ]

    matches = []

    for email in emails_found:
        score = 0

        sender = normalize_text(email["sender"])
        subject = normalize_text(email["subject"])
        snippet = normalize_text(email["snippet"])

        sender_matches = not sender_hint or sender_hint in sender
        date_matches = not date_hint or date_hint == email["date_iso"]
        keyword_matches = not search_keywords

        if sender_hint and sender_matches:
            score += 2

        for keyword in search_keywords:
            if keyword in subject:
                score += 3
                keyword_matches = True
            if keyword in snippet:
                score += 1
                keyword_matches = True

        if date_hint and date_matches:
            score += 1

        if sender_matches and keyword_matches and date_matches:
            matches.append({
                "email": email,
                "score": score,
            })

    matches.sort(key=lambda match: match["score"], reverse=True)

    return ({
        "emails_found": len(matches),
        "matches": matches
    })

    #return ejemplo:
#     {
#     "emails_found": 2,
#     "matches": [
#         {
#             "email": {
#                 "message_id": "abc123",
#                 "thread_id": "thread123",
#                 "sender": "Hernán <hernan@example.com>",
#                 "subject": "Prórroga del contrato",
#                 "date": "Fri, 26 Jun 2026 10:30:00 -0500",
#                 "date_iso": "2026-06-26",
#                 "snippet": "Te escribo para confirmar la prórroga...",
#             },
#             "score": 9,
#         },
#         {
#             "email": {
#                 "message_id": "def456",
#                 "thread_id": "thread456",
#                 "sender": "Hernán <hernan@example.com>",
#                 "subject": "Actualización del contrato",
#                 "date": "Sat, 27 Jun 2026 08:00:00 -0500",
#                 "date_iso": "2026-06-27",
#                 "snippet": "Adjunto encontrarás la actualización...",
#             },
#             "score": 6,
#         },
#     ],
# }


def score_gmail_message_candidates_by_range(emails_found: list,sender_hint: str,search_keywords: list,start_date: str | None,end_date: str | None,):

    base_result = score_gmail_message_candidates( emails_found=emails_found, sender_hint=sender_hint, search_keywords=search_keywords, date_hint=None,)

    if not start_date and not end_date:
        return base_result

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    matches = []

    for match in base_result["matches"]:
        email = match["email"]
        email_date_iso = email.get("date_iso")

        if not email_date_iso:
            continue

        email_date = date.fromisoformat(email_date_iso)

        if start <= email_date < end:
            matches.append({
                "email": email,
                "score": match["score"] + 1,
            })

    matches.sort(
        key=lambda match: match["score"],
        reverse=True,
    )

    return {
        "emails_found": len(matches),
        "matches": matches,
    }

#26 y 29
        


def score_gmail_message_candidates_MORE(emails_found: list, sender_hint: str, search_keywords: list, date_hint, ):
    return score_gmail_message_candidates(
        emails_found=emails_found,
        sender_hint=sender_hint,
        search_keywords=search_keywords,
        date_hint=date_hint,
    )



def filter_scored_matches_by_range(
    base_result: dict,
    start_date: str | None,
    end_date: str | None,
):
    if start_date is None and end_date is None:
        return base_result

    if start_date is None or end_date is None:
        raise ValueError(
            "start_date and end_date must be provided together"
        )

    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    matches = []

    for match in base_result["matches"]:
        email = match["email"]
        email_date_iso = email.get("date_iso")

        if not email_date_iso:
            continue

        email_date = date.fromisoformat(email_date_iso)

        if start <= email_date < end:
            matches.append({
                "email": email,
                "score": match["score"] + 1,
            })

    matches.sort(
        key=lambda match: match["score"],
        reverse=True,
    )

    return {
        "emails_found": len(matches),
        "matches": matches,
    }

def score_sent_gmail_message_candidates(
    emails_found: list,
    recipient_hint: str | None,
    search_keywords: list,
):
    recipient_hint = normalize_text(recipient_hint or "")

    normalized_keywords = [
        normalize_text(keyword)
        for keyword in search_keywords
    ]

    matches = []

    for email in emails_found:
        score = 0

        recipient = normalize_text(
            email.get("recipient", "")
        )
        subject = normalize_text(
            email.get("subject", "")
        )
        snippet = normalize_text(
            email.get("snippet", "")
        )

        recipient_matches = (
            not recipient_hint
            or recipient_hint in recipient
        )
        keyword_matches = not normalized_keywords

        if recipient_hint and recipient_matches:
            score += 2

        for keyword in normalized_keywords:
            if keyword in subject:
                score += 3
                keyword_matches = True

            if keyword in snippet:
                score += 1
                keyword_matches = True

        if recipient_matches and keyword_matches:
            matches.append({
                "email": email,
                "score": score,
            })

    matches.sort(
        key=lambda match: match["score"],
        reverse=True,
    )

    return {
        "emails_found": len(matches),
        "matches": matches,
    }


def score_sent_gmail_message_candidates_by_range(
    emails_found: list,
    recipient_hint: str | None,
    search_keywords: list,
    start_date: str | None,
    end_date: str | None,
):
    base_result = score_sent_gmail_message_candidates(
        emails_found=emails_found,
        recipient_hint=recipient_hint,
        search_keywords=search_keywords,
    )

    return filter_scored_matches_by_range(
        base_result=base_result,
        start_date=start_date,
        end_date=end_date,
    )


# -------------- EXTRAS ---------------

def has_real_next_page(
    access_token: str,
    next_page_token: str | None,
    query: str | None = None,
    label_id: str | None = None,
) -> bool:
    if not next_page_token:
        return False

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params: dict[str, str | int] = {
        "maxResults": 1,
        "pageToken": next_page_token,
    }

    if query:
        params["q"] = query

    if label_id:
        params["labelIds"] = label_id

    response = request_gmail(
        method="GET",
        url=GOOGLE_EMAILID_URL,
        headers=headers,
        params=params,
    )

    next_page = response.json()

    return bool(next_page.get("messages"))
