from decimal import Decimal
from datetime import datetime
from sqlalchemy import DateTime, Boolean, Integer, String, DECIMAL, ForeignKey, UniqueConstraint, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.util.datetime import utcnow

class ExchangeInstrument(Base):
    __tablename__ = "exchange_instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id", ondelete="RESTRICT"), index=True, nullable=False)
    base_asset_id  : Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), index=True, nullable=False)
    quote_asset_id : Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), index=True, nullable=False)

    exchange_symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False) 
    price_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    min_notional: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 10))

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
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))  

    exchange: Mapped["Exchange"] = relationship(back_populates="instruments")

    base_asset: Mapped["Instrument"]  = relationship(
        foreign_keys=[base_asset_id],
        back_populates="as_base_markets",
    )
    quote_asset: Mapped["Instrument"] = relationship(
        foreign_keys=[quote_asset_id],
        back_populates="as_quote_markets",
    )

    __table_args__ = (
        UniqueConstraint("exchange_id", "base_asset_id", "quote_asset_id", name="uq_market"),
        Index("ix_market_lookup", "exchange_id", "base_asset_id", "quote_asset_id"),
    )