
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.integrations.gemini_client import generate_gemini_response
from app.models.user import User
from app.repositories.conversation import create_conversation, create_message, delete_conversation, delete_conversation_messages, get_user_conversation_by_id, get_user_conversations, update_conversation_title
from app.schemas.conversation import CreateConversation, CreateMessage, UpdateConversation

#recibe current_user porque el service necesita saber quien está haciendo la acción
def create_user_conversation(body: CreateConversation, session: Session, current_user: User):
    return create_conversation(user_id=current_user.id, title=body.title, session=session)

def get_current_user_conversations(current_user: User, session: Session, limit: int, before_id: int | None):
    conversations = get_user_conversations(user_id=current_user.id, session=session, limit=limit, before_id=before_id)
    has_more = len(conversations) > limit
    items = conversations[:limit]
    return {"items": items, "next_before_id": items[-1].id if has_more else None, "has_more": has_more}

def rename_current_user_conversation(current_user: User, conversation_id: int, body: UpdateConversation, session: Session):
    if get_user_conversation_by_id(user_id=current_user.id, conversation_id=conversation_id, session=session) is None:
        raise AppError(code="conversation_not_found", message="Conversation not found.", status_code=404)
    return update_conversation_title(
        user_id=current_user.id,
        conversation_id=conversation_id,
        title=body.title,
        session=session,
        title_changed_by_user=True,
    )


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


def format_message_for_title_gemini(message: str) -> list[dict]:
    return [
        {
            "role": "user",
            "parts": [{"text": message}],
        }
    ]


def auto_generate_title_name(first_message_content: str,user_id: int, conversation_id: int, session: Session):
    message_for_conversation_title = format_message_for_title_gemini(message=first_message_content)

    system_prompt_for_title_generation = f"""Generate a short, descriptive title for a conversation based on the user's first message.

    Rules:
    - Return only the title. Do not use quotation marks, explanations, or ending punctuation.
    - Use the same language as the user.
    - Summarize the main intent instead of copying the full message.
    - Maximum 6 words and 60 characters.
    - Keep it clear, natural, and useful.
    - Do not use generic titles such as “New conversation”, “Question”, or “Help”.
    - If the message is only a greeting or is too ambiguous, create a brief descriptive title, such as “Initial greeting” or “General conversation”.
    - Do not invent details the user did not mention.

    User's first message:
    {first_message_content}""".strip()

    title_gemini_response = generate_gemini_response(messages=message_for_conversation_title, system_prompt=system_prompt_for_title_generation)



    return update_conversation_title(
        user_id=user_id,
        conversation_id=conversation_id,
        title=title_gemini_response,
        session=session,
    )
