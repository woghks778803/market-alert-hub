from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BackfillRequestItemStatus
from app.core.util.datetime import utcnow
from app.domain import MarketDTO
from app.infra.db.base import Base


class BackfillRequestItem(Base):
    __tablename__ = "backfill_request_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    backfill_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "backfill_requests.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    exchange_instrument_id: Mapped[int] = mapped_column(
        ForeignKey(
            "exchange_instruments.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[BackfillRequestItemStatus] = mapped_column(
        SAEnum(
            BackfillRequestItemStatus,
            name="backfill_request_item_status",
            values_callable=lambda e: [m.value for m in e],
            native_enum=True,
            create_constraint=True,
            validate_strings=True,
        ),
        nullable=False,
        default=BackfillRequestItemStatus.QUEUED,
        server_default=BackfillRequestItemStatus.QUEUED.value,
    )

    cursor_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    result_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_payload: Mapped[dict] = mapped_column(
        JSON, 
        nullable=False,
        default=dict,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    backfill_request: Mapped["BackfillRequest"] = relationship(
        back_populates="items",
    )
    exchange_instrument: Mapped["ExchangeInstrument"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "backfill_request_id",
            "exchange_instrument_id",
            name="uq_backfill_request_item",
        ),
        Index(
            "ix_backfill_request_items_request_status",
            "backfill_request_id",
            "status",
        ),
    )

    def to_dto(self) -> MarketDTO.BackfillRequestItem:
        return MarketDTO.BackfillRequestItem(
            id=self.id,
            backfill_request_id=self.backfill_request_id,
            exchange_instrument_id=self.exchange_instrument_id,
            status=self.status,
            cursor_at=self.cursor_at,
            result_code=self.result_code,
            result_message=self.result_message,
            result_payload=self.result_payload,
            started_at=self.started_at,
            finished_at=self.finished_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_create_dto(cls, dto: MarketDTO.BackfillRequestItemCreate) -> "BackfillRequestItem":
        return cls(
            backfill_request_id=dto.backfill_request_id,
            exchange_instrument_id=dto.exchange_instrument_id,
            status=dto.status,
            cursor_at=dto.cursor_at,
            result_code=dto.result_code,
            result_message=dto.result_message,
            result_payload=dto.result_payload,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
        )