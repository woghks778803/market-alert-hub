from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime, Enum as SAEnum, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.constants import ActiveStatus, AssetType
from app.core.datetime_utils import utcnow

class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)     # 내부 표준 심볼
    base_asset: Mapped[str] = mapped_column(String(32), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, values_callable=lambda e: [m.value for m in e], native_enum=True, create_constraint=True, validate_strings=True),
        default=AssetType.CRYPTO, server_default=AssetType.CRYPTO, nullable=False
    )
    status: Mapped[ActiveStatus] = mapped_column(
        SAEnum(ActiveStatus, values_callable=lambda e: [m.value for m in e], native_enum=True, create_constraint=True, validate_strings=True),
        default=ActiveStatus.ACTIVE, server_default=AssetType.CRYPTO, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        server_default=func.now(), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_valid:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))

    exchanges: Mapped[list["ExchangeInstrument"]] = relationship(back_populates="instrument")
