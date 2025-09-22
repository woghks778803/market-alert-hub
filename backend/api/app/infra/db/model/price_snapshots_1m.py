from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from sqlalchemy import DECIMAL, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base

class PriceSnapshot1m(Base):
    __tablename__ = "price_snapshots_1m"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    exchange_id:   Mapped[int] = mapped_column(ForeignKey("exchanges.id",  ondelete="RESTRICT"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False)
    bucket_minute: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    open:   Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    high:   Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    low:    Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    close:  Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    volume: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    __table_args__ = (
        UniqueConstraint("exchange_id", "instrument_id", "bucket_minute", name="uq_price_1m_key"),
        Index("ix_price_1m_bucket", "bucket_minute"),
        Index("ix_price_1m_instr_bucket", "instrument_id", "bucket_minute"),
    )
