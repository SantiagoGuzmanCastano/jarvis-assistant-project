from unittest.mock import Mock, patch

from app.schemas.conversation import UpdateConversation
from app.services.conversation import rename_current_user_conversation


@patch("app.services.conversation.update_conversation_title")
@patch("app.services.conversation.get_user_conversation_by_id", return_value=Mock())
def test_rename_conversation_marks_title_as_user_changed(
    conversation_mock: Mock,
    update_title_mock: Mock,
) -> None:
    session = Mock()
    current_user = Mock(id=7)

    rename_current_user_conversation(
        current_user=current_user,
        conversation_id=11,
        body=UpdateConversation(title="Plan semanal"),
        session=session,
    )

    update_title_mock.assert_called_once_with(
        user_id=7,
        conversation_id=11,
        title="Plan semanal",
        session=session,
        title_changed_by_user=True,
    )
