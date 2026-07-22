#------------------------------------------------------------

#CREACION DE MODELOS DE DB

#------------------------------------------------------------

from datetime import datetime

from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship



class User(Base):

    __tablename__ = "users"

    #Mapped[int] = tipo de variable de la columna
    #mapped_column() es donde configuras opciones extra como primary_key, nullable, index, etc.
    id: Mapped[int] = mapped_column(primary_key=True)

    #index=true:
    #se crea una estructura auxiliar donde se ordenan los emails
    #por orden alfabetico para realizar busqueda binaria en vez
    #de revisar tooodos los emails uno por uno
    #en resumen, usalo siempre que necesites buscar algo frecuentemente
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    #Este usuario tiene una propiedad llamada conversations.
    #Esa propiedad contiene sus conversaciones.
    #Cada conversación se conecta de vuelta con este usuario usando Conversation.user.

    #te devuelve una lista de conversaciones (objetos) del user
    conversations = relationship("Conversation", back_populates="user")
    external_accounts = relationship("ExternalAccount", back_populates="user")
    refresh_sessions = relationship("RefreshSession", back_populates="user")