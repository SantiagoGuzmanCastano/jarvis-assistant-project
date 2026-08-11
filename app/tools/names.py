from typing import Literal, TypeAlias


ToolName: TypeAlias = Literal[
    "get_current_time",
    "get_tools_info",
    "get_unread_emails",
    "get_latest_emails",
    "gmail_search_email_message",
    "gmail_get_drafted_emails",
    "gmail_create_email_draft",
    "gmail_search_drafted_emails",
    "gmail_read_specific_draft",
    "gmail_update_email_draft",
    "gmail_send_drafted_email",
    "gmail_create_multiple_email_drafts",
    "gmail_read_latest_email",
    "gmail_read_specific_email",
    "gmail_move_email_to_trash",
    "gmail_move_sent_email_to_trash",
    "gmail_delete_draft",
    "gmail_create_reply_draft",
    "gmail_get_sent_emails",
    "gmail_search_sent_emails",
    "calendar_create_event",
    "calendar_get_upcoming_events",
    "calendar_find_free_slots",
    "calendar_update_event",
    "calendar_delete_event",
    "calendar_prepare_event_from_email",
]

INTERNAL_TOOL_NAMES = frozenset(
    {
        "get_current_time",
        "get_tools_info",
    }
)

GMAIL_TOOL_NAMES = frozenset(
    {
        "get_latest_emails",
        "get_unread_emails",
        "gmail_create_email_draft",
        "gmail_create_multiple_email_drafts",
        "gmail_create_reply_draft",
        "gmail_delete_draft",
        "gmail_get_drafted_emails",
        "gmail_get_sent_emails",
        "gmail_move_email_to_trash",
        "gmail_move_sent_email_to_trash",
        "gmail_read_latest_email",
        "gmail_read_specific_draft",
        "gmail_read_specific_email",
        "gmail_search_drafted_emails",
        "gmail_search_email_message",
        "gmail_search_sent_emails",
        "gmail_send_drafted_email",
        "gmail_update_email_draft",
    }
)

CALENDAR_TOOL_NAMES = frozenset(
    {
        "calendar_create_event",
        "calendar_delete_event",
        "calendar_find_free_slots",
        "calendar_get_upcoming_events",
        "calendar_prepare_event_from_email",
        "calendar_update_event",
    }
)

ALL_TOOL_NAMES = frozenset(
    INTERNAL_TOOL_NAMES | GMAIL_TOOL_NAMES | CALENDAR_TOOL_NAMES
)
