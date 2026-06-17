from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text

from app.db.base import Base



#este usuario de jarvis se conecto una cuenta externa
class ExternalAccount(Base):
    __tablename__ = "external_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    #El proveedor externo, si es google, spotify, notion
    provider: Mapped[str] = mapped_column(index=True)

    #Identificador de la cuenta externa. 
    #Para Google puede ser el email
    #Para notion workspace_id o owner
    provider_account_id: Mapped[str | None] = mapped_column(nullable=True)

    encrypted_access_token: Mapped[str] = mapped_column(Text)
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    #Representa que permisos acepto el usuario
    #Los scopes son esos permisos que Google muestra en la pantalla de autorización.
    #Permiso para enviar correos, ver correos, etc etc
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)

    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    user = relationship("User", back_populates='external_accounts')
    
    