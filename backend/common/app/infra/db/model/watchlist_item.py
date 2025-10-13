from datetime import datetime
from sqlalchemy import Boolean, String, Integer, DateTime, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class WatchlistItem(Base):
    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id:       Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange_instrument_id: Mapped[int] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )

    note:       Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_deleted:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    __table_args__ = (
        # 유저 목록 정렬/조회 최적화
        Index("ix_wi_user_sort", "user_id", "sort_order"),
    )