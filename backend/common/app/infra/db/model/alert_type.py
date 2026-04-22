from datetime import datetime
from sqlalchemy import DateTime, String, Index, Integer, Boolean, text, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.constants import AlertScope
from app.core.util.datetime import utcnow
from app.infra.db.base import Base
from app.domain import AlertDTO


class AlertType(Base):
    __tablename__ = "alert_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 핵심 서비스의 타입 변경시 DB Lock 우려가 있어 enum 대신 str 처리
    scope: Mapped[str] = mapped_column(String(32), nullable=False)
    indicator: Mapped[str] = mapped_column(String(32), nullable=False)
    direction: Mapped[str | None] = mapped_column(String(32), nullable=True)
    form_type: Mapped[str] = mapped_column(String(32), nullable=False)
    param_schema: Mapped[dict] = mapped_column(JSON, nullable=False)

    sort_order: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )

    def to_dto(self) -> AlertDTO.AlertType:
        return AlertDTO.AlertType(
            id=self.id,
            code=self.code,
            name=self.name,
            scope=self.scope,
            indicator=self.indicator,
            direction=self.direction,
            form_type=self.form_type,
            param_schema=self.param_schema,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
            sort_order=self.sort_order,
            is_active=self.is_active,
        )
