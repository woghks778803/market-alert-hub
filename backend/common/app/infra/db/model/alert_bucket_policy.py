from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.util.datetime import utcnow
from app.infra.db.base import Base


class AlertBucketPolicy(Base):
    __tablename__ = "alert_bucket_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    alert_type_id: Mapped[int] = mapped_column(
        ForeignKey("alert_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exchange_instrument_id: Mapped[int | None] = mapped_column(
        ForeignKey("exchange_instruments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    bucket_size: Mapped[Decimal] = mapped_column(DECIMAL(20, 10), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    exchange_instrument: Mapped["ExchangeInstrument"] = relationship()
    alert_type: Mapped["AlertType"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "exchange_instrument_id",
            "alert_type_id",
            name="uq_alert_bucket_policy_scope",
        ),
    )