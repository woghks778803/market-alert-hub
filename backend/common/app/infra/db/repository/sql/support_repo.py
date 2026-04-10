from typing import Sequence
from sqlalchemy import select, update, delete, bindparam, desc, and_, or_, asc
from sqlalchemy.orm import Session as DbSession

from app.core.constants import NoticeCategory, FAQCategory
from app.domain import SupportDTO
from app.infra.db.model import (
    NoticeModel,
    FAQModel,
)
from ..protocol.support_repo import SupportRepo

class SqlSupportRepo(SupportRepo): 
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_notice_by_id(self, id: int, is_active: bool = True) -> SupportDTO.NoticeDetail | None: 
        stmt = select(NoticeModel).where(NoticeModel.id == id, NoticeModel.is_active.is_(is_active))
        notice = self._db.execute(stmt).scalars().one_or_none()

        if notice is None:
            return None

        prev_sql = (
            select(NoticeModel.id, NoticeModel.title)
            .where(
                NoticeModel.updated_at > notice.updated_at,
                NoticeModel.category == notice.category,
                NoticeModel.is_active.is_(is_active)
            )
            .order_by(NoticeModel.updated_at.asc())
            .limit(1)
        )

        next_sql = (
            select(NoticeModel.id, NoticeModel.title)
            .where(
                NoticeModel.updated_at < notice.updated_at,
                NoticeModel.category == notice.category,
                NoticeModel.is_active.is_(is_active)
            )
            .order_by(NoticeModel.updated_at.desc())
            .limit(1)
        )

        prev_notice = self._db.execute(prev_sql).one_or_none()
        next_notice = self._db.execute(next_sql).one_or_none()

        prev_dto = (
            SupportDTO.NoticeSimple(id=prev_notice[0], title=prev_notice[1])
            if prev_notice else None
        )

        next_dto = (
            SupportDTO.NoticeSimple(id=next_notice[0], title=next_notice[1])
            if next_notice else None
        )
        
        return notice.to_detail_dto(
            prev=prev_dto,
            next=next_dto
        )

    def list_notice_by_filter(
        self, 
        category: NoticeCategory | None, 
        is_active: bool = True, 
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SupportDTO.Notice]:
        stmt = (
            select(NoticeModel)
            .where(
                and_(
                    NoticeModel.is_active.is_(is_active),
                )
            )
            .order_by(asc(NoticeModel.id))
            .limit(limit)
            .offset(offset)
        )

        if category:
            stmt = stmt.where(NoticeModel.category == category)

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_faq_by_filter(
        self,  
        search: str | None,
        category: FAQCategory | None, 
        is_active: bool = True, 
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SupportDTO.FAQ]: 
        stmt = (
            select(FAQModel)
            .where(
                and_(
                    FAQModel.is_active.is_(is_active),
                )
            )
            .order_by(asc(FAQModel.sort_order))
            .limit(limit)
            .offset(offset)
        )

        if category:
            stmt = stmt.where(FAQModel.category == category)
        
        if search:
            stmt = stmt.where(
                or_(
                    FAQModel.question.ilike(f"%{search}%"),
                    FAQModel.answer.ilike(f"%{search}%"),
                )
            )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def update_notice_view_count(
        self,
        id: int
    ) -> int: 
        stmt = update(NoticeModel).where(NoticeModel.id == id).values(view_count=NoticeModel.view_count + 1)
        result = self._db.execute(stmt)

        return int(getattr(result, "rowcount", 0) or 0)