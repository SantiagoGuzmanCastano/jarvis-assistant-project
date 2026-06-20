from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.integrations.gemini_client import generate_gemini_response
from app.models.message import Message
from app.repositories.conversation import create_message, get_conversation_messages, get_user_conversation_by_id
from app.repositories.user_settings import get_user_settings_by_user_id
from app.services.intent_router import detect_tool_intent
from app.services.prompts import build_system_prompt
from app.services.tool_execution import build_tool_context, tool_execution_system


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
    

    last_message = create_message(
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
    
    messages = get_conversation_messages(
        conversation_id= conversation_id,
        session= session)
    
    messages_formatted = format_messages_for_gemini(messages=messages) # type: ignore


    try:
        tool_intent = detect_tool_intent(last_message_content=last_message.content)

        #tool_intent nos devolvera un objeto PYDANTIC
        #needs_tool=True tool_name='get_current_time' arguments={}
        #asi podemos acceder a needs_tool y tool_name

    
    # caso que no nos devuelva un error 
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tool intent"
            )

    if tool_intent.needs_tool:

        try:
            tool_result = tool_execution_system(tool_name=tool_intent.tool_name, arguments=tool_intent.arguments, user_id=user_id, session=session) # type: ignore
            
            #tool_result va a guardar la funcion ejecutada
            # {
            #     "current_time": "2026-06-14T..."
            # }

        except ValueError:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tool execution failed"
        )

        tool_context = build_tool_context(tool_name=tool_intent.tool_name, tool_result=tool_result) # type: ignore

        messages_with_tool_context = messages_formatted + [ # type: ignore
            {
                "role": "user",
                "parts": [
                    {
                        "text": tool_context
                    }
                ]
            }
        ]

        gemini_response = generate_gemini_response(
            messages=messages_with_tool_context,
            system_prompt=system_prompt,
        )
    
    else:
        gemini_response = generate_gemini_response(messages=messages_formatted,system_prompt=system_prompt)

    new_message = create_message(
        content=gemini_response, # type: ignore
        conversation_id=conversation_id,
        session=session, role='assistant')

    return new_message 


