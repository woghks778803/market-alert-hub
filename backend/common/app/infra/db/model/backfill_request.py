from datetime import datetime

from sqlalchemy import (
    Enum as SAEnum,
    DateTime, 
    ForeignKey, 
    Index, 
    Integer, 
    String
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.util.datetime import utcnow
from app.core.constants import CandleBaseInterval
from app.domain import MarketDTO
from app.infra.db.base import Base

class BackfillRequest(Base):
    __tablename__ = "backfill_requests"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    base: Mapped[CandleBaseInterval] = mapped_column(
        SAEnum(
            CandleBaseInterval,
            name="backfill_request_base",
            values_callable=lambda e: [m.value for m in e],
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=CandleBaseInterval.MIN_1,
        server_default=CandleBaseInterval.MIN_1.value,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

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

    user: Mapped["User"] = relationship()
    items: Mapped[list["BackfillRequestItem"]] = relationship(
        back_populates="backfill_request",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index(
            "ix_backfill_requests_created",
            "created_at",
        ),
    )

    def to_dto(self) -> MarketDTO.BackfillRequest:
        return MarketDTO.BackfillRequest(
            id=self.id,
            user_id=self.user_id,
            base=self.base,
            start_at=self.start_at,
            end_at=self.end_at,
            reason=self.reason,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def from_create_dto(cls, dto: MarketDTO.BackfillRequestCreate) -> "BackfillRequest":
        return cls(
            user_id=dto.user_id,
            base=dto.base,
            start_at=dto.start_at,
            end_at=dto.end_at,
            reason=dto.reason,
        )