from app.schemas.tools.gmail_results import (
    CreateMultipleDraftsResult,
    DraftSelectionActionResult,
    ReadEmailResult,
    ReceivedEmailListResult,
)


def test_received_email_list_result_accepts_email_summaries() -> None:
    result = ReceivedEmailListResult(
        emails=[
            {
                "sender": "ana@example.com",
                "subject": "Factura",
                "date": "2026-07-18T10:00:00-05:00",
                "snippet": "Adjunto la factura.",
            },
        ],
        returned_count=1,
        has_more=False,
    )

    assert result.emails[0].sender == "ana@example.com"
    assert result.next_page_token is None


def test_create_multiple_drafts_result_supports_partial_failures() -> None:
    result = CreateMultipleDraftsResult(
        success=False,
        reason="partial_failure",
        created_count=1,
        failed_count=1,
        results=[
            {
                "success": True,
                "draft": {
                    "draft_id": "draft-1",
                    "recipient_email": "lina@example.com",
                    "subject": "Factura",
                },
            },
            {
                "success": False,
                "reason": "missing_required_fields",
                "missing_fields": ["recipient_email"],
            },
        ],
    )

    assert result.created_count == 1
    assert result.results[1].missing_fields == ["recipient_email"]


def test_read_email_result_accepts_complete_email_content() -> None:
    result = ReadEmailResult(
        success=True,
        emails=[
            {
                "sender": "ana@example.com",
                "subject": "Factura",
                "date": "2026-07-18T10:00:00-05:00",
                "snippet": "Adjunto la factura.",
                "body": "Hola Lina, adjunto la factura completa.",
            },
        ],
    )

    assert result.success is True
    assert result.emails[0].body == "Hola Lina, adjunto la factura completa."
    assert result.matching_emails == []


def test_draft_selection_action_result_supports_multiple_matches() -> None:
    result = DraftSelectionActionResult(
        success=False,
        reason="multiple_matching_drafts",
        message="Select one draft.",
        matching_drafts=[
            {
                "draft_id": "draft-1",
                "to": "lina@example.com",
                "subject": "Factura enero",
                "date": "2026-01-15T10:00:00-05:00",
                "snippet": "Factura pendiente.",
            },
        ],
        returned_count=1,
    )

    assert result.success is False
    assert result.returned_count == 1
    assert result.matching_drafts[0].draft_id == "draft-1"
