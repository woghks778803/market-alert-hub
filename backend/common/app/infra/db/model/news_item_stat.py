from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.util.datetime import utcnow
from app.domain import NewsDTO
from app.infra.db.base import Base


class NewsItemStat(Base):
    __tablename__ = "news_item_stats"

    news_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("news_items.id"),
        primary_key=True,
    )

    click_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    share_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    last_clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

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
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def to_dto(self) -> NewsDTO.NewsItemStat:
        return NewsDTO.NewsItemStat(
            news_item_id=self.news_item_id,
            click_count=self.click_count,
            share_count=self.share_count,
            last_clicked_at=self.last_clicked_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            deleted_at=self.deleted_at,
        )