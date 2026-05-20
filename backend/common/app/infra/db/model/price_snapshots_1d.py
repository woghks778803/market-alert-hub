from datetime import datetime
from decimal import Decimal
from sqlalchemy import Integer, DECIMAL, DateTime, ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.domain import MarketDTO

class PriceSnapshot1d(Base):
    __tablename__ = "price_snapshots_1d"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

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

    def to_dto(self) -> MarketDTO.PriceSnapshot:
        return MarketDTO.PriceSnapshot(
            id=self.id,
            exchange_instrument_id=self.exchange_instrument_id,
            ts_open=self.ts_open,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
            updated_at=self.updated_at,
        )
