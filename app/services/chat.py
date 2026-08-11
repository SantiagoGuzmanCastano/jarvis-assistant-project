import logging

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.gemini_client import generate_gemini_response
from app.integrations.google_oauth import GOOGLE_CALENDAR_SCOPES
from app.models.message import Message
from app.repositories.conversation import create_message, get_recent_conversation_messages, get_user_conversation_by_id
from app.repositories.external_account import get_external_account_by_user_id_and_provider
from app.repositories.user_settings import get_user_settings_by_user_id
from app.services.conversation import auto_generate_title_name
from app.services.external_auth_service import external_account_has_scopes
from app.services.intent_router_service import detect_tool_intent
from app.services.prompts import build_system_prompt
from app.services.tool_execution import build_tool_context, tool_execution_system
from app.tools.names import CALENDAR_TOOL_NAMES, GMAIL_TOOL_NAMES


GOOGLE_CONNECTION_REQUIRED_MESSAGE = (
    "Para usar Gmail, primero conecta tu cuenta de Google desde "
    "Configuración > Cuenta Google."
)

CALENDAR_CONNECTION_REQUIRED_MESSAGE = (
    "Para usar Google Calendar, primero conecta tu cuenta de Google desde "
    "Configuración > Cuenta Google."
)

CALENDAR_RECONNECTION_REQUIRED_MESSAGE = (
    "Tu cuenta de Google no tiene los permisos de Calendar necesarios. "
    "Desconéctala y vuelve a conectarla desde Configuración > Cuenta Google."
)

logger = logging.getLogger(__name__)


def format_messages_for_gemini(messages: list[Message]) -> list:

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
        raise AppError(
            code="conversation_not_found",
            message="Conversation not found.",
            status_code=404,
        )


    user_settings = get_user_settings_by_user_id(user_id=user_id, session=session)

    if user_settings is None:
        raise AppError(
            code="user_settings_not_configured",
            message="User settings must be configured before chatting.",
            status_code=400,
        )

    has_previous_messages = bool(
        get_recent_conversation_messages(
            conversation_id=conversation_id,
            session=session,
            limit=1,
        )
    )
    if conversation.title_changed_by_user is False and not has_previous_messages:
        try:
            auto_generate_title_name(
                first_message_content=content,
                session=session,
                user_id=user_id,
                conversation_id=conversation_id,
            )
        except Exception:
            logger.exception(
                "Automatic conversation title generation failed.",
                extra={"conversation_id": conversation_id, "user_id": user_id},
            )

    system_prompt = build_system_prompt(user_settings=user_settings)
    
    messages_for_response = get_recent_conversation_messages(
        conversation_id= conversation_id,
        session= session, limit=10)
    
    
    messages_for_intent = get_recent_conversation_messages(
        conversation_id= conversation_id,
        session= session, limit=6)
    
    
    messages_for_response_formatted = format_messages_for_gemini(messages=messages_for_response) # type: ignore

    messages_for_response_formatted.append(
    {
        "role": "user",
        "parts": [{"text": content}],
    }
)

    messages_for_intent_formatted = format_messages_for_gemini(messages=messages_for_intent) # type: ignore



    try:
        tool_intent = detect_tool_intent(last_message_content=content, recent_messages_content_list=messages_for_intent_formatted)

        #tool_intent nos devolvera un objeto PYDANTIC
        #needs_tool=True tool_name='get_current_time' arguments={}
        #asi podemos acceder a needs_tool y tool_name

    
    # caso que no nos devuelva un error 
    except ValueError as error:
        raise AppError(
            code="invalid_tool_intent",
            message="The tool intent is invalid.",
            status_code=400,
        ) from error

    if tool_intent.tool_name in GMAIL_TOOL_NAMES | CALENDAR_TOOL_NAMES:
        google_account = get_external_account_by_user_id_and_provider(
            user_id=user_id,
            provider="google",
            session=session,
        )
        connection_message = None
        if google_account is None:
            connection_message = (
                CALENDAR_CONNECTION_REQUIRED_MESSAGE
                if tool_intent.tool_name in CALENDAR_TOOL_NAMES
                else GOOGLE_CONNECTION_REQUIRED_MESSAGE
            )
        elif (
            tool_intent.tool_name in CALENDAR_TOOL_NAMES
            and not external_account_has_scopes(
                external_account=google_account,
                required_scopes=GOOGLE_CALENDAR_SCOPES,
            )
        ):
            connection_message = CALENDAR_RECONNECTION_REQUIRED_MESSAGE

        if connection_message is not None:
            create_message(
                content=content,
                conversation_id=conversation_id,
                session=session,
                role="user",
            )
            return create_message(
                content=connection_message,
                conversation_id=conversation_id,
                session=session,
                role="assistant",
            )

    if tool_intent.needs_tool:

        try:
            tool_result = tool_execution_system(tool_name=tool_intent.tool_name, arguments=tool_intent.arguments, user_id=user_id, session=session, conversation_id= conversation_id) # type: ignore
            
            #tool_result va a guardar la funcion ejecutada
            # {
            #     "current_time": "2026-06-14T..."
            # }
    

        except ValueError as error:
            raise AppError(
                code="tool_execution_failed",
                message="The tool request could not be executed.",
                status_code=400,
            ) from error

        tool_context = build_tool_context(tool_name=tool_intent.tool_name, tool_result=tool_result) # type: ignore
        #el tool context tiene:
        # el resultado de la tool ejecutada
        # y las instrucciones para el llm para como responder eso


        messages_with_tool_context = messages_for_response_formatted + [ # type: ignore
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
        gemini_response = generate_gemini_response(messages=messages_for_response_formatted,system_prompt=system_prompt)

    create_message(
        content=content,
        conversation_id=conversation_id,
        session=session,
        role='user'
    )

    new_message = create_message(
        content=gemini_response, # type: ignore
        conversation_id=conversation_id,
        session=session, role='assistant')

    return new_message 


