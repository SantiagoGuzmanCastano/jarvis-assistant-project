
from datetime import datetime 
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB


from app.db.base import Base

class ConversationToolState(Base):

    __tablename__ = "conversation_tool_state"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "conversation_id",
            name="uq_conversation_tool_state_user_conversation",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    payload_json: Mapped[list | dict] = mapped_column(JSONB)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,)
    
    

