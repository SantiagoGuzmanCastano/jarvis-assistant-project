
from datetime import datetime

from app.db.base import Base
from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


class UserSettings(Base):

    __tablename__ = 'user_settings'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, unique=True)
    assistant_name: Mapped[str] = mapped_column()
    assistant_personality: Mapped[str] = mapped_column(Text) # Text le dice a la DB que este campo puede contener texto largo

    language_mode: Mapped[str] = mapped_column(default='auto')
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    

