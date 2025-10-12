from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime, Enum as SAEnum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.constants import AssetType
from app.core.datetime_utils import utcnow

class Instrument(Base):
    __tablename__ = "instruments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)     # 내부 표준 심볼
    asset_type: Mapped[AssetType] = mapped_column(
        SAEnum(AssetType, values_callable=lambda e: [m.value for m in e], native_enum=True, create_constraint=True, validate_strings=True),
        default=AssetType.CRYPTO, server_default=AssetType.CRYPTO, nullable=False
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), 
        default=utcnow, 
        onupdate=utcnow, 
        nullable=False
    )
    is_deleted:   Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))  


    as_base_markets: Mapped["ExchangeInstrument"]  = relationship(
        foreign_keys="ExchangeInstrument.base_asset_id",
        back_populates="base_asset",
    )
    as_quote_markets: Mapped["ExchangeInstrument"] = relationship(
        foreign_keys="ExchangeInstrument.quote_asset_id",
        back_populates="quote_asset",
    )
