


from datetime import datetime

from sqlalchemy import ForeignKey

from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Conversation(Base):
    __tablename__ = 'conversations'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(default="New conversation")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    #Esta conversacion tiene un usuario dueño
    #Ese usuario es un objeto de la clase "User"
    #y esta relacion se llama conversations

    # Crea la propiedad conversation.user.
    # Esa propiedad apunta al objeto User dueño de esta conversación.
    # back_populates conecta esta relación con User.conversations,
    # que será la lista de conversaciones del usuario.

    #te devuelve el obejeto USER , dueño de la conversacion
    user = relationship("User", back_populates="conversations")

    #apunta a los mensaje de la conversacion
    messages = relationship("Message", back_populates="conversation")

