from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.gemini_client import generate_gemini_response
from app.models.message import Message
from app.repositories.conversation import create_message, get_conversation_messages, get_user_conversation_by_id
from app.repositories.user_settings import get_user_settings_by_user_id
from app.services.prompts import build_system_prompt


def format_messages_for_gemini(messages: list[Message]):

    gemini_messages = []

    for message in messages:
        role = 'model' if message.role == 'assistant' else 'user'
        gemini_messages.append({
            'role': role,
            'parts': [{'text': message.content}]
        })

    return gemini_messages



def create_chat_response(conversation_id: int, user_id: int, session: Session, content: str):
    
    conversation=get_user_conversation_by_id(user_id=user_id, conversation_id=conversation_id, session=session)

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Conversation not found'
        )
    

    create_message(
        content=content,
        conversation_id=conversation_id,
        session=session,
        role='user'
    )
    


    user_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if user_settings is None:
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User settings must be configured before chatting",
    )

    system_prompt = build_system_prompt(user_settings=user_settings)
    print(system_prompt)

    messages = get_conversation_messages(
        conversation_id= conversation_id,
        session= session)
    
    messages_formatted = format_messages_for_gemini(messages=messages)


    gemini_response = generate_gemini_response(messages=messages_formatted,system_prompt=system_prompt)

    new_message = create_message(
        content=gemini_response,
        conversation_id=conversation_id,
        session=session, role='assistant')

    return new_message 



