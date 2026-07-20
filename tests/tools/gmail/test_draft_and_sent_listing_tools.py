from unittest.mock import Mock, patch

from app.tools.external.gmail.draft_listings import (
    gmail_get_drafted_emails_tool,
    gmail_search_drafted_emails_tool,
)
from app.tools.external.gmail.sent_email_listings import gmail_get_sent_emails_tool


@patch("app.tools.external.gmail.draft_listings.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail.draft_listings.get_valid_google_access_token")
def test_get_drafted_emails_uses_draft_list_arguments(
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
) -> None:
    session = Mock()
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {"drafts": [], "returned_count": 0}

    result = gmail_get_drafted_emails_tool(
        arguments={"max_results": 5},
        user_id=7,
        session=session,
    )

    fetch_drafts_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="",
    )
    assert result == {"drafts": [], "returned_count": 0}


@patch("app.tools.external.gmail.draft_listings.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail.draft_listings.get_valid_google_access_token")
@patch("app.tools.external.gmail.draft_listings.build_gmail_query")
def test_search_drafted_emails_uses_recipient_search_arguments(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
) -> None:
    session = Mock()
    build_query_mock.return_value = "to:lina@example.com factura"
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {"drafts": [], "returned_count": 0}

    result = gmail_search_drafted_emails_tool(
        arguments={
            "recipient_hint": ["Lina"],
            "search_keywords": ["factura"],
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "max_results": 5,
        },
        user_id=7,
        session=session,
    )

    build_query_mock.assert_called_once_with(
        search_scope="draft",
        start_date="2026-01-01",
        end_date="2026-02-01",
        search_keywords=["factura"],
        recipient_hint=["Lina"],
    )
    fetch_drafts_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="to:lina@example.com factura",
    )
    assert result == {"drafts": [], "returned_count": 0}


@patch("app.tools.external.gmail.sent_email_listings.fetch_sent_gmail_messages")
@patch("app.tools.external.gmail.sent_email_listings.get_valid_google_access_token")
def test_get_sent_emails_uses_max_results_arguments(
    access_token_mock: Mock,
    fetch_sent_mock: Mock,
) -> None:
    session = Mock()
    access_token_mock.return_value = "access-token"
    fetch_sent_mock.return_value = {"emails": [], "returned_count": 0}

    result = gmail_get_sent_emails_tool(
        arguments={"max_results": 5},
        user_id=7,
        session=session,
    )

    fetch_sent_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
    )
    assert result == {"emails": [], "returned_count": 0}
