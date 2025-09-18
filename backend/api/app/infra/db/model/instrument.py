from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base

class AssetType(str, enum.Enum):
    crypto = "CRYPTO"; fx = "FX"; stock = "STOCK"; future = "FUTURE"

class InstrumentStatus(str, enum.Enum):
    active = "active"; inactive = "inactive"

class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)     # 내부 표준 심볼
    base_asset: Mapped[str] = mapped_column(String(32), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, native_enum=False, create_constraint=True, validate_strings=True),
        default=AssetType.crypto, nullable=False
    )
    status: Mapped[InstrumentStatus] = mapped_column(
        SAEnum(InstrumentStatus, native_enum=False, create_constraint=True, validate_strings=True),
        default=InstrumentStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exchanges: Mapped[list["ExchangeInstrument"]] = relationship(back_populates="instrument")
