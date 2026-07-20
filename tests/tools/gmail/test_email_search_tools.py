from unittest.mock import Mock, patch

from app.tools.external.gmail.received_email_listings import (
    get_latest_emails_tool,
    get_unread_emails_tool,
    gmail_search_email_message_tool,
)


@patch("app.tools.external.gmail.received_email_listings.format_gmail_message_metadata")
@patch("app.tools.external.gmail.received_email_listings.fetch_unread_gmail_messages")
@patch("app.tools.external.gmail.received_email_listings.get_valid_google_access_token")
@patch("app.tools.external.gmail.received_email_listings.build_gmail_query")
def test_get_unread_emails_uses_email_search_arguments(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_unread_mock: Mock,
    format_messages_mock: Mock,
) -> None:
    session = Mock()
    build_query_mock.return_value = "is:unread from:ana@example.com"
    access_token_mock.return_value = "access-token"
    fetch_unread_mock.return_value = {
        "emails": [{"id": "message-1"}],
        "has_more": False,
        "next_page_token": None,
    }
    format_messages_mock.return_value = [
        {"sender": "ana@example.com", "subject": "Factura", "date": "", "snippet": ""},
    ]

    result = get_unread_emails_tool(
        arguments={
            "sender_hint": ["Ana"],
            "search_keywords": ["factura"],
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "max_results": 5,
        },
        user_id=7,
        session=session,
    )

    build_query_mock.assert_called_once_with(
        search_scope="unread",
        start_date="2026-01-01",
        end_date="2026-02-01",
        search_keywords=["factura"],
        sender_hint=["Ana"],
        recipient_hint=None,
    )
    fetch_unread_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="is:unread from:ana@example.com",
    )
    assert result["returned_count"] == 1


@patch("app.tools.external.gmail.received_email_listings.format_gmail_message_metadata")
@patch("app.tools.external.gmail.received_email_listings.fetch_latest_gmail_messages")
@patch("app.tools.external.gmail.received_email_listings.get_valid_google_access_token")
def test_get_latest_emails_uses_max_results_arguments(
    access_token_mock: Mock,
    fetch_latest_mock: Mock,
    format_messages_mock: Mock,
) -> None:
    session = Mock()
    access_token_mock.return_value = "access-token"
    fetch_latest_mock.return_value = {
        "emails": [{"id": "message-1"}],
        "returned_count": 1,
        "has_more": True,
        "next_page_token": "next-page-token",
    }
    format_messages_mock.return_value = [
        {"sender": "ana@example.com", "subject": "Factura", "date": "", "snippet": ""},
    ]

    result = get_latest_emails_tool(
        arguments={"max_results": 5},
        user_id=7,
        session=session,
    )

    fetch_latest_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
    )
    assert result["returned_count"] == 1
    assert result["next_page_token"] == "next-page-token"


@patch("app.tools.external.gmail.received_email_listings.fetch_specific_gmail_message_format_FSD")
@patch("app.tools.external.gmail.received_email_listings.get_valid_google_access_token")
@patch("app.tools.external.gmail.received_email_listings.build_gmail_query")
def test_search_email_message_uses_email_search_arguments(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_messages_mock: Mock,
) -> None:
    session = Mock()
    build_query_mock.return_value = "from:ana@example.com factura"
    access_token_mock.return_value = "access-token"
    fetch_messages_mock.return_value = {
        "emails": [{"message_id": "message-1", "subject": "Factura"}],
        "returned_count": 1,
        "has_more": False,
    }

    result = gmail_search_email_message_tool(
        arguments={
            "sender_hint": ["Ana"],
            "search_keywords": ["factura"],
            "max_results": 5,
        },
        user_id=7,
        session=session,
    )

    build_query_mock.assert_called_once_with(
        search_scope="received",
        start_date="",
        end_date="",
        search_keywords=["factura"],
        sender_hint=["Ana"],
        recipient_hint=None,
    )
    fetch_messages_mock.assert_called_once_with(
        access_token="access-token",
        query="from:ana@example.com factura",
        max_results=5,
    )
    assert result["returned_count"] == 1
