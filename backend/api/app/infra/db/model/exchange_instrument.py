from __future__ import annotations
from decimal import Decimal
from sqlalchemy import Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base

class ExchangeInstrument(Base):
    __tablename__ = "exchange_instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id", ondelete="RESTRICT"), index=True, nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id", ondelete="RESTRICT"), index=True, nullable=False)

    exchange_symbol: Mapped[str] = mapped_column(String(64), index=True, nullable=False)  # 거래소 표기
    price_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    qty_precision: Mapped[int] = mapped_column(Integer, nullable=False)
    min_notional: Mapped[Decimal | None] = mapped_column(DECIMAL(20, 10))
    active: Mapped[int] = mapped_column(Integer, nullable=False)  # MySQL TINYINT(1) 매핑

    exchange: Mapped["Exchange"] = relationship(back_populates="instruments")
    instrument: Mapped["Instrument"] = relationship(back_populates="exchanges")
