from app.schemas.tools.gmail import (
    CreateDraftArguments,
    CreateMultipleDraftsArguments,
    CreateReplyDraftArguments,
    DeleteDraftArguments,
    DraftListArguments,
    EmailSearchArguments,
    MaxResultsArguments,
    MoveEmailToTrashArguments,
    MoveSentEmailToTrashArguments,
    ReadLatestEmailArguments,
    ReadSpecificDraftArguments,
    ReadSpecificEmailArguments,
    RecipientSearchArguments,
    SendDraftArguments,
    UpdateDraftArguments,
)
from app.tools.external.gmail_tools import (
    get_latest_emails_tool,
    get_unread_emails_tool,
    gmail_create_email_draft_tool,
    gmail_create_multiple_email_drafts_tool,
    gmail_create_reply_draft_tool,
    gmail_delete_draft_tool,
    gmail_get_drafted_emails_tool,
    gmail_get_sent_emails_tool,
    gmail_move_email_to_trash_tool,
    gmail_move_sent_email_to_trash_tool,
    gmail_read_latest_email_tool,
    gmail_read_specific_draft_tool,
    gmail_read_specific_email_tool,
    gmail_search_drafted_emails_tool,
    gmail_search_email_message_tool,
    gmail_search_sent_emails_tool,
    gmail_send_drafted_email_tool,
    gmail_update_email_draft_tool,
)
from app.tools.internal.current_time import get_current_time


TOOLS = {
    "get_current_time": {
        "function": get_current_time,
        "arguments_schema": None,
    },
    "get_unread_emails": {
        "function": get_unread_emails_tool,
        "arguments_schema": EmailSearchArguments,
    },
    "get_latest_emails": {
        "function": get_latest_emails_tool,
        "arguments_schema": MaxResultsArguments,
    },
    "gmail_search_email_message": {
        "function": gmail_search_email_message_tool,
        "arguments_schema": EmailSearchArguments,
    },
    "gmail_create_email_draft": {
        "function": gmail_create_email_draft_tool,
        "arguments_schema": CreateDraftArguments,
    },
    "gmail_get_drafted_emails": {
        "function": gmail_get_drafted_emails_tool,
        "arguments_schema": DraftListArguments,
    },
    "gmail_search_drafted_emails": {
        "function": gmail_search_drafted_emails_tool,
        "arguments_schema": RecipientSearchArguments,
    },
    "gmail_send_drafted_email": {
        "function": gmail_send_drafted_email_tool,
        "arguments_schema": SendDraftArguments,
    },
    "gmail_create_multiple_email_drafts": {
        "function": gmail_create_multiple_email_drafts_tool,
        "arguments_schema": CreateMultipleDraftsArguments,
    },
    "gmail_read_latest_email": {
        "function": gmail_read_latest_email_tool,
        "arguments_schema": ReadLatestEmailArguments,
    },
    "gmail_read_specific_email": {
        "function": gmail_read_specific_email_tool,
        "arguments_schema": ReadSpecificEmailArguments,
    },
    "gmail_read_specific_draft": {
        "function": gmail_read_specific_draft_tool,
        "arguments_schema": ReadSpecificDraftArguments,
    },
    "gmail_move_email_to_trash": {
        "function": gmail_move_email_to_trash_tool,
        "arguments_schema": MoveEmailToTrashArguments,
    },
    "gmail_move_sent_email_to_trash": {
        "function": gmail_move_sent_email_to_trash_tool,
        "arguments_schema": MoveSentEmailToTrashArguments,
    },
    "gmail_delete_draft": {
        "function": gmail_delete_draft_tool,
        "arguments_schema": DeleteDraftArguments,
    },
    "gmail_update_email_draft": {
        "function": gmail_update_email_draft_tool,
        "arguments_schema": UpdateDraftArguments,
    },
    "gmail_create_reply_draft": {
        "function": gmail_create_reply_draft_tool,
        "arguments_schema": CreateReplyDraftArguments,
    },
    "gmail_get_sent_emails": {
        "function": gmail_get_sent_emails_tool,
        "arguments_schema": MaxResultsArguments,
    },
    "gmail_search_sent_emails": {
        "function": gmail_search_sent_emails_tool,
        "arguments_schema": RecipientSearchArguments,
    },
}
