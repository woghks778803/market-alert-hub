from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, Integer, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.infra.db.base import Base
from app.domain import OutboxDTO


class OutboxAttempt(Base):
    __tablename__ = "outbox_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    outbox_id: Mapped[int] = mapped_column(
        ForeignKey("outboxs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)

    # 핵심 결과 요약만
    success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retryable: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    result_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_payload: Mapped[dict] = mapped_column(
        JSON, 
        nullable=False, 
        default=dict,
    )

    # 타이밍
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ux_outbox_attempt", "outbox_id", "attempt_no", unique=True),
        Index("ix_attempts_outbox_time", "outbox_id", "started_at"),
    )

    def to_dto(self) -> OutboxDTO.OutboxAttempt:
        """
        ORM Model -> domain DTO (조회/반환용)
        """
        return OutboxDTO.OutboxAttempt(
            id=self.id,
            outbox_id=self.outbox_id,
            attempt_no=self.attempt_no,
            success=self.success,
            retryable=self.retryable,
            result_code=self.result_code,
            result_message=self.result_message,
            result_payload=self.result_payload,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )

    @classmethod
    def from_create_dto(cls, dto: OutboxDTO.OutboxAttemptCreate) -> "OutboxAttempt":
        """
        domain DTO -> ORM Model
        """
        return cls(
            outbox_id=dto.outbox_id,
            attempt_no=dto.attempt_no,
            success=dto.success,
            retryable=dto.retryable,
            result_code=dto.result_code,
            result_message=dto.result_message,
            result_payload=dto.result_payload,
            started_at=dto.started_at,
            finished_at=dto.finished_at,
        )
