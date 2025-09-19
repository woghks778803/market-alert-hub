from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DECIMAL, DateTime, ForeignKey, PrimaryKeyConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class PriceLatest(Base):
    __tablename__ = "prices_latest"

    exchange_id: Mapped[int]   = mapped_column(ForeignKey("exchanges.id",  ondelete="RESTRICT"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)

    last_price:  Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    volume_24h:  Mapped[Decimal | None] = mapped_column(DECIMAL(32, 16))
    high_24h:    Mapped[Decimal | None] = mapped_column(DECIMAL(32, 16))
    low_24h:     Mapped[Decimal | None] = mapped_column(DECIMAL(32, 16))
    ts:          Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("exchange_id", "instrument_id", name="pk_prices_latest"),
        Index("ix_prices_latest_ts", "ts"),
        Index("ix_prices_latest_instrument", "instrument_id"),
    )
