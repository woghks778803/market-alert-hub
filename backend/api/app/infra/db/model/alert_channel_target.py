from __future__ import annotations
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infra.db.base import Base

class AlertChannelTarget(Base):
    __tablename__ = "alert_channel_targets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    alert_id:       Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_channel_id: Mapped[int] = mapped_column(ForeignKey("user_channels.id", ondelete="CASCADE"), nullable=False, index=True)

    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)

    alert:        Mapped["Alert"]       = relationship(back_populates="channels")
    user_channel: Mapped["UserChannel"] = relationship(back_populates="targets")

    __table_args__ = (UniqueConstraint("alert_id", "user_channel_id", name="uq_alert_channel_target"),)
