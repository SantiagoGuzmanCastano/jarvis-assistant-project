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
        conversation_id=11,
    )

    fetch_drafts_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="",
    )
    assert result == {"drafts": [], "returned_count": 0}


@patch("app.tools.external.gmail.draft_listings.create_tool_state")
@patch("app.tools.external.gmail.draft_listings.format_gmail_draft_full")
@patch("app.tools.external.gmail.draft_listings.fetch_gmail_draft_full")
@patch("app.tools.external.gmail.draft_listings.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail.draft_listings.get_valid_google_access_token")
def test_single_recent_draft_sets_active_draft(
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
    fetch_full_draft_mock: Mock,
    format_draft_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    draft_summary = {
        "position": 1,
        "draft_id": "draft-1",
        "to": "lina@example.com",
        "subject": "Factura",
        "date": "2026-01-15T10:00:00-05:00",
        "snippet": "Factura.",
    }
    active_draft = {**draft_summary, "body": "Contenido completo."}
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {
        "drafts": [draft_summary],
        "returned_count": 1,
        "has_more": False,
    }
    fetch_full_draft_mock.return_value = {"id": "draft-1"}
    format_draft_mock.return_value = active_draft

    result = gmail_get_drafted_emails_tool(
        arguments={"max_results": 1},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["drafts"] == [draft_summary]
    fetch_full_draft_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-1",
    )
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_draft",
        payload={"active_draft": active_draft},
    )


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
        conversation_id=11,
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


@patch("app.tools.external.gmail.draft_listings.create_tool_state")
@patch("app.tools.external.gmail.draft_listings.format_gmail_draft_full")
@patch("app.tools.external.gmail.draft_listings.fetch_gmail_draft_full")
@patch("app.tools.external.gmail.draft_listings.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail.draft_listings.get_valid_google_access_token")
@patch("app.tools.external.gmail.draft_listings.build_gmail_query")
def test_single_draft_search_sets_active_draft(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
    fetch_full_draft_mock: Mock,
    format_draft_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    draft_summary = {
        "position": 1,
        "draft_id": "draft-1",
        "to": "lina@example.com",
        "subject": "Factura",
        "date": "2026-01-15T10:00:00-05:00",
        "snippet": "Factura.",
    }
    active_draft = {**draft_summary, "body": "Contenido completo."}
    build_query_mock.return_value = "to:lina@example.com factura"
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {
        "drafts": [draft_summary],
        "returned_count": 1,
        "has_more": False,
    }
    fetch_full_draft_mock.return_value = {"id": "draft-1"}
    format_draft_mock.return_value = active_draft

    result = gmail_search_drafted_emails_tool(
        arguments={"recipient_hint": ["Lina"]},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    assert result["drafts"] == [draft_summary]
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_active_draft",
        payload={"active_draft": active_draft},
    )


@patch("app.tools.external.gmail.draft_listings.create_tool_state")
@patch("app.tools.external.gmail.draft_listings.fetch_gmail_draft_full")
@patch("app.tools.external.gmail.draft_listings.fetch_specific_gmail_drafts")
@patch("app.tools.external.gmail.draft_listings.get_valid_google_access_token")
@patch("app.tools.external.gmail.draft_listings.build_gmail_query")
def test_multiple_draft_searches_keep_selection_state(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_drafts_mock: Mock,
    fetch_full_draft_mock: Mock,
    create_state_mock: Mock,
) -> None:
    session = Mock()
    drafts = [
        {
            "position": 1,
            "draft_id": "draft-1",
            "to": "lina@example.com",
            "subject": "Factura enero",
            "date": "2026-01-15T10:00:00-05:00",
            "snippet": "Factura enero.",
        },
        {
            "position": 2,
            "draft_id": "draft-2",
            "to": "lina@example.com",
            "subject": "Factura febrero",
            "date": "2026-02-15T10:00:00-05:00",
            "snippet": "Factura febrero.",
        },
    ]
    build_query_mock.return_value = "to:lina@example.com factura"
    access_token_mock.return_value = "access-token"
    fetch_drafts_mock.return_value = {
        "drafts": drafts,
        "returned_count": 2,
        "has_more": False,
    }

    gmail_search_drafted_emails_tool(
        arguments={"recipient_hint": ["Lina"]},
        user_id=7,
        session=session,
        conversation_id=11,
    )

    fetch_full_draft_mock.assert_not_called()
    create_state_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        session=session,
        state_type="gmail_draft_selection",
        payload={"drafts": drafts},
    )


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
