
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import ForeignKey

from app.db.base import Base


class ConversationToolState(Base):

    __tablename__ = "conversation_tool_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    payload_json: Mapped[list[dict]] = mapped_column(JSONB)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    

