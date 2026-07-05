


from app.tools.external.gmail_tools import gmail_create_reply_draft_tool, gmail_create_email_draft_tool, gmail_create_multiple_email_drafts_tool, gmail_get_drafted_emails_tool, gmail_read_latest_email_tool, gmail_read_specific_email_tool, gmail_search_drafted_emails_tool, gmail_search_email_message_tool, gmail_send_drafted_email_tool, get_latest_emails_tool, get_unread_emails_tool, gmail_update_email_draft_tool
from app.tools.internal.current_time import get_current_time


# queremos guardar la funcion, no su resultado por eso
# no se pone el parentesis

TOOLS = {
    "get_current_time": get_current_time,
    
    "get_unread_emails": get_unread_emails_tool,
    "get_latest_emails": get_latest_emails_tool,

    "gmail_search_email_message": gmail_search_email_message_tool,

    "gmail_create_email_draft": gmail_create_email_draft_tool,
    "gmail_get_drafted_emails": gmail_get_drafted_emails_tool,
    "gmail_search_drafted_emails":gmail_search_drafted_emails_tool,
    "gmail_send_drafted_email": gmail_send_drafted_email_tool,
    "gmail_create_multiple_email_drafts": gmail_create_multiple_email_drafts_tool,
    "gmail_read_latest_email": gmail_read_latest_email_tool,
    "gmail_read_specific_email":gmail_read_specific_email_tool,
    "gmail_update_email_draft": gmail_update_email_draft_tool,
    "gmail_create_reply_draft": gmail_create_reply_draft_tool

}

    # "gmail_send_email_message":gmail_send_email_message_tool,
