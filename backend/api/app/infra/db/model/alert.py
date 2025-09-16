from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from app.infra.db.base import Base
import enum


class AlertStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"


class AlertType(str, enum.Enum):
    price_above = "price_above"
    price_below = "price_below"
    cross_up = "cross_up"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name = Column(String(100), nullable=False)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.active)
    type = Column(Enum(AlertType), nullable=False)
    params = Column(JSON, nullable=True)  # 조건 파라미터 (임시 JSON 저장)
    last_fired_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
