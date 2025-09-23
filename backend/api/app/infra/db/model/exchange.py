from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime, Enum as SAEnum, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.constants import ActiveStatus
from app.core.datetime_utils import utcnow

class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)    
    base_url: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ActiveStatus] = mapped_column(
        SAEnum(ActiveStatus, native_enum=True, create_constraint=True, validate_strings=True),
        default=ActiveStatus.ACTIVE, server_default=ActiveStatus.ACTIVE, nullable=False
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

    instruments: Mapped[list["ExchangeInstrument"]] = relationship(back_populates="exchange")