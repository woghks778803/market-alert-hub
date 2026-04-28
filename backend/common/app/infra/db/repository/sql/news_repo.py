from typing import Sequence
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import aliased, Session as DbSession
from app.domain import NewsDTO
from app.infra.db.model import (
    RssProviderModel,
    RssSourceModel,
    NewsItemModel,
    NewsItemStatModel,
    NewsItemTranslationModel,
)
from app.infra.db.repository.protocol.news_repo import NewsRepo

rp = RssProviderModel
rs = RssSourceModel
ni = NewsItemModel
nis = NewsItemStatModel
nit = NewsItemTranslationModel

class SqlNewsRepo(NewsRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def list_rss_source_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NewsDTO.RssSource]: 
        stmt = (
            select(rs)
            .select_from(rs)
            .join(rp, rp.id == rs.rss_provider_id)
            .where(
                and_(
                    rs.is_active.is_(is_active),
                    
                    rp.is_active.is_(True),
                    rp.deleted_at.is_(None),
                )
            )
            .order_by(asc(rs.id))
            .limit(limit)
            .offset(offset)
        )

        if deleted_is_null:
            stmt = stmt.where(rs.deleted_at.is_(None))

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]
