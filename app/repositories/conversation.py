from datetime import datetime, timedelta, timezone

from fastapi import HTTPException,status
from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Session
from app.core.config import settings


from app.models.conversation import Conversation
from app.models.generic_tool_state import ConversationToolState
from app.models.message import Message


def create_conversation(user_id: int, title: str, session: Session):
    new_conversation = Conversation(
        user_id= user_id,
        title=title
    )
    session.add(new_conversation)
    session.commit()
    session.refresh(new_conversation)
    return new_conversation


def get_user_conversations(user_id: int, session: Session):
    
    query = select(Conversation).where(Conversation.user_id==user_id).order_by(Conversation.created_at.desc())
    conversations_list = session.scalars(query).all()

    return conversations_list


def get_user_conversation_by_id(user_id: int, conversation_id: int, session: Session):

    query = select(Conversation).where(Conversation.user_id==user_id, Conversation.id==conversation_id)
    return session.scalars(query).first()

def create_message(content: str, conversation_id: int, session: Session, role: str):
    new_message = Message(
        content=content,
        conversation_id=conversation_id,
        role=role
    )

    #session.add sabe donde insertar la tabla por la clase del objeto
    #new_message es una instancia de Message y Message tiene
    #tablename = messages
    session.add(new_message)
    session.commit()
    session.refresh(new_message)
    return new_message


def get_conversation_messages(conversation_id: int, session: Session, limit: int):

    query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at).limit(limit=limit)
    return session.scalars(query).all()


def get_recent_conversation_messages(conversation_id: int, session: Session, limit: int) -> list:

    query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)

    #DB devuelve:
    # mensaje 10
    # mensaje 9
    # mensaje 8
    messages = session.scalars(query).all()

    # Prompt necesita:
    # mensaje 8
    # mensaje 9
    # mensaje 10
    return list(reversed(messages))

    

    
def delete_conversation(conversation_id:int, session: Session):

    query = delete(Conversation).where(Conversation.id == conversation_id)

    session.execute(query)
    session.commit()


def delete_conversation_messages(conversation_id: int, session: Session):


    query = delete(Message).where(
    Message.conversation_id == conversation_id)
    session.execute(query)
    session.commit()


def create_tool_state(payload: dict | list, user_id: int, session: Session, conversation_id: int):
    
    existing_tool_state = get_tool_state(user_id=user_id,session=session, conversation_id=conversation_id)

    if existing_tool_state is not None:
        session.delete(existing_tool_state)
        session.flush()

    now = datetime.now(timezone.utc)

    new_tool_state = ConversationToolState(
        user_id=user_id,
        conversation_id= conversation_id,
        payload_json=payload,
        created_at=now,
        expires_at=now + timedelta(minutes=settings.tool_state_expire_minutes),
        )

    session.add(new_tool_state)
    session.commit()
    session.refresh(new_tool_state)

    return new_tool_state


# def get_tool_payload(user_id: int, session: Session, conversation_id: int):
#     query = select(ConversationToolState.payload_json).where(
#         ConversationToolState.user_id == user_id,
#         ConversationToolState.conversation_id == conversation_id,
#     )

#     return session.scalars(query).first()


def get_tool_state(user_id: int, session: Session, conversation_id: int):
    query = select(ConversationToolState).where(
        ConversationToolState.user_id == user_id,
        ConversationToolState.conversation_id == conversation_id,
    )

    return session.scalars(query).first()

def delete_tool_state(user_id: int, conversation_id: int,session: Session):
    query = delete(ConversationToolState).where(
        ConversationToolState.user_id == user_id,
        ConversationToolState.conversation_id == conversation_id,
    )
    session.execute(query)
    session.commit()


def get_tool_payload(user_id: int, session: Session, conversation_id: int):
    tool_state = get_tool_state(user_id=user_id,session=session, conversation_id=conversation_id)

    now = datetime.now(timezone.utc)

    if tool_state is None:
        return None
    
    if now >= tool_state.expires_at:
        delete_tool_state(user_id=user_id,conversation_id=conversation_id,session=session)
        return None

    return tool_state.payload_json



