
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

from app.db.base import Base



class Message(Base):

    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)

    #a que conversacion pertenece este mensaje
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    #te devuelve el objeto conversation, te diec a que conversation pertenece este mensaje
    conversation = relationship('Conversation', back_populates="messages")