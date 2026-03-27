from datetime import datetime
from decimal import Decimal

from sqlalchemy import Integer, DECIMAL, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.domain import MarketDTO


class ExchangeInstrumentTicker(Base):
    __tablename__ = "exchange_instrument_tickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    exchange_instrument_id: Mapped[int] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    open_price: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    high_24h: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    low_24h: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    volume_24h: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    price_change_24h: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    price_change_rate_24h: Mapped[Decimal] = mapped_column(
        DECIMAL(32, 16), nullable=False
    )

    normalized_price: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)
    normalized_volume: Mapped[Decimal] = mapped_column(DECIMAL(32, 16), nullable=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "exchange_instrument_id", name="uq_ticker_exchange_instrument"
        ),
        Index("ix_ticker_exchange_instrument", "exchange_instrument_id"),
    )

    def to_dto(self) -> MarketDTO.ExchangeInstrumentTicker:
        return MarketDTO.ExchangeInstrumentTicker(
            id=self.id,
            exchange_instrument_id=self.exchange_instrument_id,
            open_price=self.open_price,
            close_price=self.close_price,
            high_24h=self.high_24h,
            low_24h=self.low_24h,
            volume_24h=self.volume_24h,
            price_change_24h=self.price_change_24h,
            price_change_rate_24h=self.price_change_rate_24h,
            normalized_price=self.normalized_price,
            normalized_volume=self.normalized_volume,
            updated_at=self.updated_at,
        )
