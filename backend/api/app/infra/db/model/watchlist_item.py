from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id:       Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False, index=True)
    exchange_id:   Mapped[int] = mapped_column(ForeignKey("exchanges.id",   ondelete="RESTRICT"), nullable=False, index=True)

    note:       Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    is_valid:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))