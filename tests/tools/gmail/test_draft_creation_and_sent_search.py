from unittest.mock import Mock, patch

from app.tools.external.gmail_tools import (
    gmail_create_email_draft_tool,
    gmail_create_multiple_email_drafts_tool,
    gmail_search_sent_emails_tool,
)


@patch("app.tools.external.gmail_tools.create_gmail_draft")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_create_email_draft_uses_complete_create_draft_arguments(
    access_token_mock: Mock,
    create_draft_mock: Mock,
) -> None:
    session = Mock()
    access_token_mock.return_value = "access-token"
    create_draft_mock.return_value = {"id": "draft-1"}

    result = gmail_create_email_draft_tool(
        arguments={
            "recipient_email": "lina@example.com",
            "subject": "Factura",
            "body": "Adjunto la factura.",
        },
        user_id=7,
        session=session,
    )

    create_draft_mock.assert_called_once_with(
        access_token="access-token",
        recipient_email="lina@example.com",
        subject="Factura",
        body="Adjunto la factura.",
    )
    assert result == {
        "success": True,
        "draft": {
            "draft_id": "draft-1",
            "recipient_email": "lina@example.com",
            "subject": "Factura",
        },
    }


@patch("app.tools.external.gmail_tools.create_gmail_draft")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
def test_create_multiple_email_drafts_allows_partial_failures(
    access_token_mock: Mock,
    create_draft_mock: Mock,
) -> None:
    access_token_mock.return_value = "access-token"
    create_draft_mock.return_value = {"id": "draft-1"}

    result = gmail_create_multiple_email_drafts_tool(
        arguments={
            "to_create": 2,
            "to_create_list": [
                {
                    "recipient_email": "lina@example.com",
                    "subject": "Factura",
                    "body": "Adjunto la factura.",
                },
                {
                    "subject": "Sin destinatario",
                },
            ],
        },
        user_id=7,
        session=Mock(),
    )

    assert result["created_count"] == 1
    assert result["failed_count"] == 1
    assert result["success"] is False
    assert result["reason"] == "partial_failure"
    assert result["results"][0]["draft"]["draft_id"] == "draft-1"
    assert result["results"][1]["missing_fields"] == ["recipient_email", "body"]
    create_draft_mock.assert_called_once()


@patch("app.tools.external.gmail_tools.fetch_specific_sent_gmail_messages")
@patch("app.tools.external.gmail_tools.get_valid_google_access_token")
@patch("app.tools.external.gmail_tools.build_gmail_query")
def test_search_sent_emails_uses_recipient_search_arguments(
    build_query_mock: Mock,
    access_token_mock: Mock,
    fetch_sent_mock: Mock,
) -> None:
    build_query_mock.return_value = "to:lina@example.com factura"
    access_token_mock.return_value = "access-token"
    fetch_sent_mock.return_value = {
        "emails": [],
        "returned_count": 0,
        "has_more": False,
    }

    result = gmail_search_sent_emails_tool(
        arguments={
            "recipient_hint": ["Lina"],
            "search_keywords": ["factura"],
            "max_results": 5,
        },
        user_id=7,
        session=Mock(),
    )

    build_query_mock.assert_called_once_with(
        search_scope="sent",
        start_date="",
        end_date="",
        search_keywords=["factura"],
        recipient_hint=["Lina"],
        sender_hint=None,
    )
    fetch_sent_mock.assert_called_once_with(
        access_token="access-token",
        query="to:lina@example.com factura",
        max_results=5,
    )
    assert result["returned_count"] == 0
