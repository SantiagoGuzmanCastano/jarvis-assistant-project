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
from app.schemas.tools.gmail_results import (
    CreateDraftResult,
    CreateMultipleDraftsResult,
    CurrentTimeResult,
    DeleteDraftResult,
    DraftListResult,
    ReadDraftResult,
    ReadEmailResult,
    ReceivedEmailListResult,
    ReceivedEmailTrashResult,
    ReplyDraftResult,
    SendDraftResult,
    SentEmailListResult,
    SentEmailTrashResult,
    UpdateDraftResult,
)
from app.tools.external.gmail.draft_deletion import gmail_delete_draft_tool
from app.tools.external.gmail.draft_reading import gmail_read_specific_draft_tool
from app.tools.external.gmail.draft_updates import gmail_update_email_draft_tool
from app.tools.external.gmail.reply_drafts import gmail_create_reply_draft_tool
from app.tools.external.gmail.received_email_actions import gmail_move_email_to_trash_tool
from app.tools.external.gmail.sent_email_actions import gmail_move_sent_email_to_trash_tool
from app.tools.external.gmail.received_email_reading import (
    gmail_read_latest_email_tool,
    gmail_read_specific_email_tool,
)
from app.tools.external.gmail.draft_sending import gmail_send_drafted_email_tool
from app.tools.external.gmail.draft_creation import (
    gmail_create_email_draft_tool,
    gmail_create_multiple_email_drafts_tool,
)
from app.tools.external.gmail.sent_email_listings import (
    gmail_get_sent_emails_tool,
    gmail_search_sent_emails_tool,
)
from app.tools.external.gmail.received_email_listings import (
    get_latest_emails_tool,
    get_unread_emails_tool,
    gmail_search_email_message_tool,
)
from app.tools.external.gmail.draft_listings import (
    gmail_get_drafted_emails_tool,
    gmail_search_drafted_emails_tool,
)
from app.tools.internal.current_time import get_current_time


TOOLS = {
    "get_current_time": {
        "function": get_current_time,
        "arguments_schema": None,
        "result_schema": CurrentTimeResult,
    },
    "get_unread_emails": {
        "function": get_unread_emails_tool,
        "arguments_schema": EmailSearchArguments,
        "result_schema": ReceivedEmailListResult,
    },
    "get_latest_emails": {
        "function": get_latest_emails_tool,
        "arguments_schema": MaxResultsArguments,
        "result_schema": ReceivedEmailListResult,
    },
    "gmail_search_email_message": {
        "function": gmail_search_email_message_tool,
        "arguments_schema": EmailSearchArguments,
        "result_schema": ReceivedEmailListResult,
    },
    "gmail_create_email_draft": {
        "function": gmail_create_email_draft_tool,
        "arguments_schema": CreateDraftArguments,
        "result_schema": CreateDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_get_drafted_emails": {
        "function": gmail_get_drafted_emails_tool,
        "arguments_schema": DraftListArguments,
        "result_schema": DraftListResult,
        "requires_conversation_id": True,
    },
    "gmail_search_drafted_emails": {
        "function": gmail_search_drafted_emails_tool,
        "arguments_schema": RecipientSearchArguments,
        "result_schema": DraftListResult,
        "requires_conversation_id": True,
    },
    "gmail_send_drafted_email": {
        "function": gmail_send_drafted_email_tool,
        "arguments_schema": SendDraftArguments,
        "result_schema": SendDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_create_multiple_email_drafts": {
        "function": gmail_create_multiple_email_drafts_tool,
        "arguments_schema": CreateMultipleDraftsArguments,
        "result_schema": CreateMultipleDraftsResult,
    },
    "gmail_read_latest_email": {
        "function": gmail_read_latest_email_tool,
        "arguments_schema": ReadLatestEmailArguments,
        "result_schema": ReadEmailResult,
    },
    "gmail_read_specific_email": {
        "function": gmail_read_specific_email_tool,
        "arguments_schema": ReadSpecificEmailArguments,
        "result_schema": ReadEmailResult,
        "requires_conversation_id": True,
    },
    "gmail_read_specific_draft": {
        "function": gmail_read_specific_draft_tool,
        "arguments_schema": ReadSpecificDraftArguments,
        "result_schema": ReadDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_move_email_to_trash": {
        "function": gmail_move_email_to_trash_tool,
        "arguments_schema": MoveEmailToTrashArguments,
        "result_schema": ReceivedEmailTrashResult,
        "requires_conversation_id": True,
    },
    "gmail_move_sent_email_to_trash": {
        "function": gmail_move_sent_email_to_trash_tool,
        "arguments_schema": MoveSentEmailToTrashArguments,
        "result_schema": SentEmailTrashResult,
        "requires_conversation_id": True,
    },
    "gmail_delete_draft": {
        "function": gmail_delete_draft_tool,
        "arguments_schema": DeleteDraftArguments,
        "result_schema": DeleteDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_update_email_draft": {
        "function": gmail_update_email_draft_tool,
        "arguments_schema": UpdateDraftArguments,
        "result_schema": UpdateDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_create_reply_draft": {
        "function": gmail_create_reply_draft_tool,
        "arguments_schema": CreateReplyDraftArguments,
        "result_schema": ReplyDraftResult,
        "requires_conversation_id": True,
    },
    "gmail_get_sent_emails": {
        "function": gmail_get_sent_emails_tool,
        "arguments_schema": MaxResultsArguments,
        "result_schema": SentEmailListResult,
    },
    "gmail_search_sent_emails": {
        "function": gmail_search_sent_emails_tool,
        "arguments_schema": RecipientSearchArguments,
        "result_schema": SentEmailListResult,
    },
}
