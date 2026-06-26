


from app.tools.external.gmail_tools import gmail_create_email_draft_tool, gmail_create_multiple_email_drafts_tool, gmail_get_drafted_emails_tool, gmail_search_drafted_emails_tool, gmail_search_email_message_tool, gmail_send_drafted_email_tool, read_latest_emails_tool, read_unread_emails_tool
from app.tools.internal.current_time import get_current_time


# queremos guardar la funcion, no su resultado por eso
# no se pone el parentesis

TOOLS = {
    "get_current_time": get_current_time,
    "read_unread_emails": read_unread_emails_tool,
    "read_latest_emails": read_latest_emails_tool,

    "gmail_search_email_message": gmail_search_email_message_tool,

    "gmail_create_email_draft": gmail_create_email_draft_tool,
    "gmail_get_drafted_emails": gmail_get_drafted_emails_tool,
    "gmail_search_drafted_emails":gmail_search_drafted_emails_tool,
    "gmail_send_drafted_email": gmail_send_drafted_email_tool,
    "gmail_create_multiple_email_drafts": gmail_create_multiple_email_drafts_tool,

}

    # "gmail_send_email_message":gmail_send_email_message_tool,
