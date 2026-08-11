from unittest.mock import Mock

from app.integrations.gmail import drafts as gmail_drafts


def _draft_resource(draft_id: str, subject: str) -> dict:
    return {
        "id": draft_id,
        "message": {
            "snippet": "",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": subject},
                    {"name": "To", "value": "lina@example.com"},
                ],
            },
        },
    }


def test_draft_search_does_not_run_fallback_when_exact_query_matches(
    monkeypatch,
) -> None:
    list_mock = Mock(
        return_value={
            "drafts": [{"id": "draft-1"}],
            "resultSizeEstimate": 1,
        }
    )
    metadata_mock = Mock(
        return_value=_draft_resource("draft-1", "Tecnología")
    )
    full_mock = Mock()
    monkeypatch.setattr(gmail_drafts, "fetch_gmail_drafts_ids", list_mock)
    monkeypatch.setattr(
        gmail_drafts,
        "fetch_gmail_draft_metadata",
        metadata_mock,
    )
    monkeypatch.setattr(gmail_drafts, "fetch_gmail_draft_full", full_mock)

    result = gmail_drafts.fetch_specific_gmail_drafts(
        access_token="access-token",
        max_results=5,
        query="in:drafts tecnologia",
        search_keywords=["tecnologia"],
    )

    assert result["returned_count"] == 1
    list_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="in:drafts tecnologia",
    )
    metadata_mock.assert_called_once_with(
        access_token="access-token",
        draft_id="draft-1",
    )
    full_mock.assert_not_called()


def test_draft_search_runs_accent_insensitive_fallback_after_zero_results(
    monkeypatch,
) -> None:
    list_mock = Mock(
        side_effect=[
            {"drafts": [], "resultSizeEstimate": 0},
            {
                "drafts": [{"id": "draft-1"}],
                "resultSizeEstimate": 1,
            },
        ]
    )
    full_mock = Mock(
        return_value=_draft_resource(
            "draft-1",
            "Tecnología en Odontopediatría",
        )
    )
    metadata_mock = Mock()
    monkeypatch.setattr(gmail_drafts, "fetch_gmail_drafts_ids", list_mock)
    monkeypatch.setattr(gmail_drafts, "fetch_gmail_draft_full", full_mock)
    monkeypatch.setattr(
        gmail_drafts,
        "fetch_gmail_draft_metadata",
        metadata_mock,
    )

    result = gmail_drafts.fetch_specific_gmail_drafts(
        access_token="access-token",
        max_results=5,
        query="in:drafts (tecnologia OR odontopediatria)",
        search_keywords=["tecnologia", "odontopediatria"],
    )

    assert result["returned_count"] == 1
    assert result["drafts"][0]["subject"] == (
        "Tecnología en Odontopediatría"
    )
    assert list_mock.call_args_list[0].kwargs == {
        "access_token": "access-token",
        "max_results": 5,
        "query": "in:drafts (tecnologia OR odontopediatria)",
    }
    assert list_mock.call_args_list[1].kwargs == {
        "access_token": "access-token",
        "max_results": gmail_drafts.GMAIL_DRAFT_FALLBACK_SCAN_LIMIT,
        "query": "in:drafts",
    }
    full_mock.assert_called_once_with(
        "draft-1",
        access_token="access-token",
    )
    metadata_mock.assert_not_called()


def test_draft_search_without_keywords_keeps_original_zero_result(
    monkeypatch,
) -> None:
    list_mock = Mock(
        return_value={"drafts": [], "resultSizeEstimate": 0}
    )
    monkeypatch.setattr(gmail_drafts, "fetch_gmail_drafts_ids", list_mock)

    result = gmail_drafts.fetch_specific_gmail_drafts(
        access_token="access-token",
        max_results=5,
        query="in:drafts",
    )

    assert result["returned_count"] == 0
    list_mock.assert_called_once()
