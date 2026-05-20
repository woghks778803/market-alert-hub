from datetime import datetime
from sqlalchemy import Integer, String, Text, Boolean, DateTime, Index, Enum as SAEnum, text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base
from app.core.util.datetime import utcnow
from app.core.constants import NoticeCategory  
from app.domain import SupportDTO

class Notice(Base):
    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=True)  
    content: Mapped[str] = mapped_column(Text, nullable=False)  
    category: Mapped[str] = mapped_column(SAEnum(NoticeCategory, values_callable=lambda e: [m.value for m in e],
                                                            native_enum=True, create_constraint=True, validate_strings=True),
                                                            default=NoticeCategory.NOTICE, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("0"))
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    __table_args__ = (
        Index("ix_notice_category_active", "category", "is_active"),
        Index("ix_notice_created_at", "created_at"),
    )

    def to_dto(self) -> SupportDTO.Notice:
        return SupportDTO.Notice(
            id=self.id,
            title=self.title,
            content=self.content,
            category=self.category,
            is_active=self.is_active,
            view_count=self.view_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_detail_dto(self, prev=None, next=None):
        return SupportDTO.NoticeDetail(
            id=self.id,
            title=self.title,
            summary=self.summary,
            content=self.content,
            category=self.category,
            is_active=self.is_active,
            view_count=self.view_count,
            created_at=self.created_at,
            updated_at=self.updated_at,
            prev=prev,
            next=next,
        )