from datetime import datetime
from sqlalchemy import Boolean, Integer, String, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base
from app.core.datetime_utils import utcnow

class Exchange(Base):
    __tablename__ = "exchanges"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(64))
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", nullable=False)    
    base_url: Mapped[str | None] = mapped_column(String(255))
    
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

    instruments: Mapped[list["ExchangeInstrument"]] = relationship(back_populates="exchange")