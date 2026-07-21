
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.user import User
from app.repositories.conversation import create_conversation, create_message, delete_conversation, delete_conversation_messages, get_user_conversation_by_id, get_user_conversations
from app.schemas.conversation import CreateConversation, CreateMessage

#recibe current_user porque el service necesita saber quien está haciendo la acción
def create_user_conversation(body: CreateConversation, session: Session, current_user: User):
    return create_conversation(user_id=current_user.id, title=body.title, session=session)

def get_current_user_conversations(current_user: User, session: Session):
    return get_user_conversations(user_id=current_user.id, session=session)


#buscar conversación por conversation_id + current_user.id
def get_user_conversation_detail(current_user: User, conversation_id: int, session: Session):

    conversation_exists = get_user_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id, session=session)

    if conversation_exists is None:
        raise AppError(
            code="conversation_not_found",
            message="Conversation not found.",
            status_code=404,
        )
    
    return conversation_exists


def create_user_message(current_user: User ,conversation_id: int, session: Session, body: CreateMessage):

    conversation_exists = get_user_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id, session=session)

    if conversation_exists is None:
        raise AppError(
            code="conversation_not_found",
            message="Conversation not found.",
            status_code=404,
        )
    
    new_message = create_message(content=body.content, conversation_id=conversation_id, session=session, role="user")

    return new_message


def delete_current_user_conversation(user_id: int,conversation_id: int, session: Session):

    conversation_exists = get_user_conversation_by_id(user_id=user_id, conversation_id=conversation_id, session=session)

    if conversation_exists is None:
        raise AppError(
            code="conversation_not_found",
            message="Conversation not found.",
            status_code=404,
        )

    delete_conversation_messages(conversation_id=conversation_id, session=session)
    
    delete_conversation(conversation_id= conversation_id, session=session)

