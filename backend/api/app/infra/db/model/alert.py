from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, func
from app.infra.db.base import Base

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    target_price: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # "above"/"below"
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

