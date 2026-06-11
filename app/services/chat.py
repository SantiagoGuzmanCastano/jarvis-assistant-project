from fastapi import HTTPException, status
from sqlalchemy.orm import Session



from app.integrations.gemini_client import generate_gemini_response
from app.models.message import Message
from app.repositories.conversation import create_message, get_conversation_messages, get_user_conversation_by_id


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
    
    messages = get_conversation_messages(
        conversation_id= conversation_id,
        session= session)
    


    messages_formatted = format_messages_for_gemini(messages=messages)

    gemini_response = generate_gemini_response(messages=messages_formatted)

    new_message = create_message(
        content=gemini_response,
        conversation_id=conversation_id,
        session=session, role='assistant')

    return new_message 