from unittest.mock import Mock, patch

from app.integrations.gmail.drafts import GOOGLE_UPDATEDRAFTS_URL, update_gmail_draft


@patch("app.integrations.gmail.drafts.request_gmail")
def test_update_gmail_draft_sends_the_draft_id_in_its_payload(
    request_gmail_mock: Mock,
) -> None:
    response_mock = Mock()
    response_mock.json.return_value = {"id": "draft-1"}
    request_gmail_mock.return_value = response_mock

    result = update_gmail_draft(
        access_token="access-token",
        body="Contenido actualizado.",
        subject="Asunto actualizado",
        recipient_email="lina@example.com",
        draft_id="draft-1",
    )

    assert result == {"id": "draft-1"}
    request_arguments = request_gmail_mock.call_args.kwargs
    assert request_arguments["method"] == "PUT"
    assert request_arguments["url"] == f"{GOOGLE_UPDATEDRAFTS_URL}/draft-1"
    assert request_arguments["json"]["id"] == "draft-1"
    assert request_arguments["json"]["message"]["raw"]
