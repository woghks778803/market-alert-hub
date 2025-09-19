from __future__ import annotations
import enum
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base

class ExchangeStatus(str, enum.Enum):
    active = "active"; inactive = "inactive"

class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)    
    base_url: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ExchangeStatus] = mapped_column(
        SAEnum(ExchangeStatus, native_enum=True, create_constraint=True, validate_strings=True),
        default=ExchangeStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    instruments: Mapped[list["ExchangeInstrument"]] = relationship(back_populates="exchange")