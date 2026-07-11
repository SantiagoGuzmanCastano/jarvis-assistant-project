


from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo

def build_gmail_query(search_scope: str, start_date: str | None, end_date:str | None, search_keywords: list[str] | None, sender_hint: list[str] | None = None, recipient_hint: list[str] | None = None,) -> str:
#"(from:Hernán OR from:Hernan) (reunión OR reunion OR reuniones) after:YYYY-MM-DD before:YYYY-MM-DD"

    base_query_parts = ["category:primary",]
    user_timezone = ZoneInfo("America/Bogota")

    query_parts = []
    
    if sender_hint:
        sender_terms = [
            f'from:"{sender}"'
            for sender in sender_hint
        ]

        query_parts.append(
            f"({' OR '.join(sender_terms)})"
        )

    if recipient_hint:
        recipient_terms = [
            f'to:"{sender}"'
            for sender in recipient_hint
        ]

        query_parts.append(
            f"({' OR '.join(recipient_terms)})"
        )

    if start_date:
        start_datetime = datetime.combine(
                date.fromisoformat(start_date),
                time.min,
                tzinfo=user_timezone,
            )
        query_parts.append(f"after:{int(start_datetime.timestamp())}")

    if end_date:
        end_datetime = datetime.combine(
            date.fromisoformat(end_date),
            time.min,
            tzinfo=user_timezone,)
        query_parts.append(f"before:{int(end_datetime.timestamp())}")

    if search_keywords:
        query_parts.append(
            f"({' OR '.join(search_keywords)})"
        )

    query = base_query_parts + query_parts

    if search_scope == "unread":
        unread_query_parts = ["in:inbox","is:unread"]
        built_query = unread_query_parts + query  
        return " ".join(built_query)

    if search_scope == "received":
        received_query_parts = ["in:inbox",]
        built_query = received_query_parts + query  
        return " ".join(built_query)
        
    if search_scope == "sent":
        sent_query_parts = ["in:sent"]
        built_query = sent_query_parts + query_parts
        return " ".join(built_query)

    if search_scope == "draft":
        draft_query_parts = ["in:drafts"]

        if recipient_hint:
            draft_recipient_terms = []

            for recipient in recipient_hint:
                if "@" in recipient:
                    draft_recipient_terms.append(f'to:"{recipient}"')
                    draft_recipient_terms.append(f'"{recipient}"')
                else:
                    draft_recipient_terms.append(f'"{recipient}"')

            draft_query_parts.append(
                f"({' OR '.join(draft_recipient_terms)})"
            )

        if start_date:
            start_datetime = datetime.combine(
                date.fromisoformat(start_date),
                time.min,
                tzinfo=user_timezone,
            )
            draft_query_parts.append(f"after:{int(start_datetime.timestamp())}")

        if end_date:
            end_datetime = datetime.combine(
                date.fromisoformat(end_date),
                time.min,
                tzinfo=user_timezone,
            )
            draft_query_parts.append(f"before:{int(end_datetime.timestamp())}")

        if search_keywords:
            draft_query_parts.append(
                f"({' OR '.join(search_keywords)})"
            )

        return " ".join(draft_query_parts)
    
    return " ".join(base_query_parts + query_parts)
    




def change_date_format (start_date: str, end_date: str):
    user_timezone = ZoneInfo("America/Bogota")

    if start_date:
        start_datetime = datetime.combine(
                date.fromisoformat(start_date),
                time.min,
                tzinfo=user_timezone,
            )
        return ({
        "start_date_formatted": start_datetime,
        "end_date_formatted": end_datetime
    })
    if end_date:
        end_datetime = datetime.combine(
            date.fromisoformat(end_date),
            time.min,
            tzinfo=user_timezone,)
        
    return ({
        "start_date_formatted": start_datetime,
        "end_date_formatted": end_datetime
    })
