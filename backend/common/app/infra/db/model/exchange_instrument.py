from decimal import Decimal
from datetime import datetime
from sqlalchemy import (
    DateTime,
    Boolean,
    Integer,
    String,
    DECIMAL,
    ForeignKey,
    UniqueConstraint,
    Index,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.domain import MarketDTO


class ExchangeInstrument(Base):
    __tablename__ = "exchange_instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(
        ForeignKey("exchanges.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    base_asset_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    quote_asset_id: Mapped[int] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    exchange_symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    price_precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qty_precision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_notional: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 10), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    exchange: Mapped["Exchange"] = relationship(back_populates="instruments")

    base_asset: Mapped["Instrument"] = relationship(
        foreign_keys=[base_asset_id],
        back_populates="as_base_markets",
    )
    quote_asset: Mapped["Instrument"] = relationship(
        foreign_keys=[quote_asset_id],
        back_populates="as_quote_markets",
    )

    __table_args__ = (
        UniqueConstraint(
            "exchange_id", "base_asset_id", "quote_asset_id", name="uq_market"
        ),
        Index("ix_market_lookup", "exchange_id", "base_asset_id", "quote_asset_id"),
    )

    def to_dto(self) -> MarketDTO.ExchangeInstrument:
        return MarketDTO.ExchangeInstrument(
            id=self.id,
            exchange_id=self.exchange_id,
            base_asset_id=self.base_asset_id,
            quote_asset_id=self.quote_asset_id,
            exchange_symbol=self.exchange_symbol,
            price_precision=self.price_precision,
            qty_precision=self.qty_precision,
            min_notional=self.min_notional,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            is_active=self.is_active,
        )

    # @classmethod
    # def from_create_dto(cls, dto: MarketDTO.ExchangeInstrumentCreate) -> "ExchangeInstrument":
    #     return cls(

    #     )
