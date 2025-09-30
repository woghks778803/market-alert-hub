from datetime import datetime
from decimal import Decimal
from sqlalchemy import DECIMAL, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class PriceSnapshot1d(Base):
    __tablename__ = "price_snapshots_1d"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    exchange_instrument_id: Mapped[int] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    ts_open: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    open:   Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    high:   Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    low:    Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    close:  Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    volume: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow, onupdate=utcnow, nullable=False
    )

    __table_args__ = (
        UniqueConstraint("exchange_instrument_id", "ts_open", name="uq_price_1d_exi_ts"),
        Index("ix_price_1d_exi_ts", "exchange_instrument_id", "ts_open"),
    )
