from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id:    Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True) 

    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_addr: Mapped[str | None] = mapped_column(String(45))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("ix_sessions_expires", "expires_at"),)
