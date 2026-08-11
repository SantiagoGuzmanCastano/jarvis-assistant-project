from unittest.mock import Mock

from app.integrations.gmail import sent as gmail_sent


def _sent_message(message_id: str, subject: str) -> dict:
    return {
        "id": message_id,
        "threadId": f"thread-{message_id}",
        "snippet": "Detalles de la reunión",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "To", "value": "ana@example.com"},
                {"name": "Subject", "value": subject},
                {
                    "name": "Date",
                    "value": "Wed, 29 Jul 2026 10:00:00 -0500",
                },
            ],
            "body": {"data": "UmV1bmnDs24="},
        },
    }


def test_sent_search_does_not_run_fallback_when_exact_query_matches(
    monkeypatch,
) -> None:
    list_mock = Mock(
        return_value={"messages": [{"id": "sent-1"}]}
    )
    metadata_mock = Mock(
        return_value=_sent_message("sent-1", "Tecnología")
    )
    full_mock = Mock()
    monkeypatch.setattr(
        gmail_sent,
        "fetch_specific_sent_gmail_messages_ids",
        list_mock,
    )
    monkeypatch.setattr(
        gmail_sent,
        "fetch_metadata_FSD_sent_gmail_message",
        metadata_mock,
    )
    monkeypatch.setattr(
        gmail_sent,
        "fetch_full_specific_gmail_messages_metadata",
        full_mock,
    )

    result = gmail_sent.fetch_specific_sent_gmail_messages(
        access_token="access-token",
        max_results=5,
        query="in:sent tecnologia",
        search_keywords=["tecnologia"],
    )

    assert result["returned_count"] == 1
    list_mock.assert_called_once_with(
        access_token="access-token",
        max_results=5,
        query="in:sent tecnologia",
    )
    metadata_mock.assert_called_once()
    full_mock.assert_not_called()


def test_sent_search_runs_accent_insensitive_fallback_after_zero_results(
    monkeypatch,
) -> None:
    list_mock = Mock(
        side_effect=[
            {"messages": []},
            {"messages": [{"id": "sent-1"}]},
        ]
    )
    full_mock = Mock(
        return_value=_sent_message(
            "sent-1",
            "Tecnología en Odontopediatría",
        )
    )
    metadata_mock = Mock()
    monkeypatch.setattr(
        gmail_sent,
        "fetch_specific_sent_gmail_messages_ids",
        list_mock,
    )
    monkeypatch.setattr(
        gmail_sent,
        "fetch_full_specific_gmail_messages_metadata",
        full_mock,
    )
    monkeypatch.setattr(
        gmail_sent,
        "fetch_metadata_FSD_sent_gmail_message",
        metadata_mock,
    )

    result = gmail_sent.fetch_specific_sent_gmail_messages(
        access_token="access-token",
        max_results=5,
        query="in:sent (tecnologia OR odontopediatria)",
        search_keywords=["tecnologia", "odontopediatria"],
    )

    assert result["returned_count"] == 1
    assert result["emails"][0]["subject"] == (
        "Tecnología en Odontopediatría"
    )
    assert list_mock.call_args_list[1].kwargs == {
        "access_token": "access-token",
        "max_results": gmail_sent.GMAIL_SENT_FALLBACK_SCAN_LIMIT,
        "query": "in:sent",
    }
    full_mock.assert_called_once_with(
        "sent-1",
        access_token="access-token",
    )
    metadata_mock.assert_not_called()
