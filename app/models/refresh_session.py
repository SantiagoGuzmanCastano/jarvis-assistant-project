#------------------------------------------------------------

#CREACION DE MODELOS DE DB

#------------------------------------------------------------

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey

from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship



class RefreshSession(Base):

    __tablename__ = "refresh_sessions"


    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    token_hash: Mapped[str] = mapped_column(unique=True,index=True,)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),default=lambda: datetime.now(timezone.utc),nullable=False,)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),nullable=False,)

    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True,)

    user = relationship("User", back_populates="refresh_sessions")