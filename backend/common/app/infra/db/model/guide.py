from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base
from app.core.util.datetime import utcnow

class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Tiptap HTML
    
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    
    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)