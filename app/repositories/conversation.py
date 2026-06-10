from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
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