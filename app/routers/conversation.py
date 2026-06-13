from fastapi import APIRouter, Depends, HTTPException,status

from app.db.session import SessionDep
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.conversation import ConversationResponse, ConversationWithMessages, CreateConversation, CreateMessage, DeleteConversation, MessageResponse
from app.services.conversation import create_user_conversation, create_user_message, delete_current_user_conversation, get_current_user_conversations, get_user_conversation_detail

#el tags sirve para que en los docs los endpoints de conversation salgan bajo del titulo
#que esta en tags, o sea conversations
router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post('', response_model=ConversationResponse)
def create_new_conversation(body: CreateConversation, session: SessionDep, current_user: User = Depends(get_current_user)):
    new_conversation = create_user_conversation(body=body, session=session, current_user=current_user)
    return new_conversation

@router.get('', response_model=list[ConversationResponse])
def list_user_conversations(session: SessionDep, current_user: User = Depends(get_current_user)):
    conversations=get_current_user_conversations(current_user=current_user, session=session)
    return conversations

@router.get('/{conversation_id}', response_model=ConversationWithMessages)
def get_current_user_conversation_by_id(conversation_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):

    user_conversation = get_user_conversation_detail(current_user=current_user, conversation_id=conversation_id, session=session)
    return user_conversation

@router.post('/{conversation_id}/messages', response_model=MessageResponse)
def create_new_conversation_message(body: CreateMessage,conversation_id: int, session: SessionDep, current_user: User = Depends(get_current_user)):

    new_message = create_user_message(current_user=current_user, conversation_id=conversation_id, session=session, body=body)

    return new_message

@router.delete('/{conversation_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_user_conversation(session: SessionDep,conversation_id: int, current_user: User = Depends(get_current_user)):
    delete_current_user_conversation(user_id=current_user.id, session=session, conversation_id=conversation_id)
    return