
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.conversation import create_conversation, create_message, get_user_conversation_by_id, get_user_conversations
from app.schemas.conversation import CreateConversation, CreateMessage

#recibe current_user porque el service necesita saber quien está haciendo la acción
def create_user_conversation(body: CreateConversation, session: Session, current_user: User):
    return create_conversation(user_id=current_user.id, title=body.title, session=session)

def get_current_user_conversations(current_user: User, session: Session):
    return get_user_conversations(user_id=current_user.id, session=session)


#buscar conversación por conversation_id + current_user.id
def get_user_conversation_detail(current_user: User, conversation_id: int, session: Session):

    response = get_user_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id, session=session)

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Conversation not found'
        )
    
    return response


def create_user_message(current_user: User ,conversation_id: int, session: Session, body: CreateMessage):

    response = get_user_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id, session=session)

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Conversation not found'
        )
    
    new_message = create_message(content=body.content, conversation_id=conversation_id, session=session, role="user")

    return new_message