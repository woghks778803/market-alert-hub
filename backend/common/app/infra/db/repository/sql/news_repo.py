from typing import cast, Sequence
from datetime import datetime
from sqlalchemy.engine import CursorResult
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, tuple_
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.orm import aliased, Session as DbSession

from app.core.constants import (
    TranslationCode,
    LanguageCode, 
    NewsItemTranslationStatus, 
    NewsItemStatus
)
from app.domain import NewsDTO
from app.infra.db.model import (
    RssProviderModel,
    RssSourceModel,
    NewsItemModel,
    NewsItemStatModel,
    NewsItemTranslationModel,
)
from app.infra.db.repository.protocol.news_repo import NewsRepo
from app.infra.db.utils import to_row_dict

rp = RssProviderModel
rs = RssSourceModel
ni = NewsItemModel
nis = NewsItemStatModel
nit = NewsItemTranslationModel

class SqlNewsRepo(NewsRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def list_news_item_translation_by_filter(
        self,
        *,
        rss_source_id: int,
        locale: LanguageCode,
        translation_status: NewsItemTranslationStatus,
        item_status: NewsItemStatus,
    ) -> list[NewsDTO.NewsItemTranslationTarget]: 

        stmt = (
            select(
                nit.id.label("translation_id"),
                ni.id.label("news_item_id"),
                ni.title_original.label("title_original"),
                ni.description_original.label("description_original"),
                rp.language.label("provider_language"),
                ni.language.label("item_language"),
            )
            .select_from(nit)
            .join(ni, ni.id == nit.news_item_id)
            .join(rs, rs.id == ni.rss_source_id)
            .join(rp, rp.id == rs.rss_provider_id)
            .where(
                and_(
                    nit.locale == locale,
                    nit.status == translation_status,
                    ni.status == item_status,
                    rs.id == rss_source_id,

                    ni.deleted_at.is_(None),
                    rs.is_active.is_(True),
                    rs.deleted_at.is_(None),
                    rp.is_active.is_(True),
                    rp.deleted_at.is_(None),
                )
            )
        )

        rows = self._db.execute(stmt)
        return [
            NewsDTO.NewsItemTranslationTarget(**row)
            for row in rows.mappings().all() 
        ]

    def list_news_item_by_link_fingerprints(
        self,
        *,
        rss_source_id: int,
        link_fingerprints: list[bytes],
    ) -> list[NewsDTO.NewsItem]:
        if not link_fingerprints:
            return []

        stmt = (
            select(ni)
            .where(
                and_(
                    ni.rss_source_id == rss_source_id,
                    ni.link_fingerprint.in_(link_fingerprints),
                )
            )
        )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_news_feed_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NewsDTO.NewsFeed]: 
        stmt = (
            select(rs, rp)
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

        rows = self._db.execute(stmt).all()
        return [
            NewsDTO.NewsFeed(
                rss_source_id=source.id,
                rss_provider_id=provider.id,

                rss_source_code=source.code,
                rss_source_name=source.name,
                feed_url=source.feed_url,
                etag=source.etag,
                last_modified=source.last_modified,

                rss_provider_code=provider.code,
                rss_provider_name=provider.name,
                language=provider.language,
                request_timeout_sec=provider.request_timeout_sec,
                rate_limit_policy=provider.rate_limit_policy,
                retry_policy=provider.retry_policy,
            )
            for source, provider in rows
        ]


    def get_news_feed_by_id(
        self,
        rss_source_id: int,
        is_active: bool = True,
        deleted_is_null: bool = True,
    ) -> NewsDTO.NewsFeed | None:
        stmt = (
            select(rs, rp)
            .select_from(rs)
            .join(rp, rp.id == rs.rss_provider_id)
            .where(
                and_(
                    rs.id == rss_source_id,
                    rs.is_active.is_(is_active),
                    
                    rp.is_active.is_(True),
                    rp.deleted_at.is_(None),
                )
            )
        )

        if deleted_is_null:
            stmt = stmt.where(rs.deleted_at.is_(None))

        row = self._db.execute(stmt).first()

        if not row:
            return None

        source, provider = row

        return NewsDTO.NewsFeed(
            rss_source_id=source.id,
            rss_provider_id=provider.id,
            rss_source_code=source.code,
            rss_source_name=source.name,
            feed_url=source.feed_url,
            etag=source.etag,
            last_modified=source.last_modified,
            rss_provider_code=provider.code,
            rss_provider_name=provider.name,
            language=provider.language,
            request_timeout_sec=provider.request_timeout_sec,
            rate_limit_policy=provider.rate_limit_policy,
            retry_policy=provider.retry_policy,
        )

    def add_news_item_stats(
        self,
        rows: list[NewsDTO.NewsItemTranslationCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        if not rows:
            return

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(x) for x in chunk]

            stmt = insert(nis).values(values)
            self._db.execute(stmt)
        

    def add_news_item_translations(
        self,
        rows: list[NewsDTO.NewsItemTranslationCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        if not rows:
            return

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(x) for x in chunk]

            stmt = insert(nit).values(values)
            self._db.execute(stmt)


    def upsert_news_items(
        self,
        rows: list[NewsDTO.NewsItemCreate],
        *,
        chunk_size: int = 1000,
    ) -> None:
        if not rows:
            return

        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            values = [to_row_dict(x) for x in chunk]

            stmt = mysql_insert(ni).values(values)

            stmt = stmt.on_duplicate_key_update(
                guid=func.coalesce(ni.guid, stmt.inserted.guid), # null일때만 갱신
                link=stmt.inserted.link,
                canonical_link=stmt.inserted.canonical_link,
                title_original=stmt.inserted.title_original,
                description_original=stmt.inserted.description_original,
                content_original=stmt.inserted.content_original,
                image_url=stmt.inserted.image_url,
                author=stmt.inserted.author,
                language=stmt.inserted.language,
                published_at=stmt.inserted.published_at,
                fetched_at=stmt.inserted.fetched_at,
                status=stmt.inserted.status,
            )

            self._db.execute(stmt)


    def update_rss_source(
        self,
        *,
        rss_source_id: int,
        etag: str | None,
        last_modified: str | None,
        deleted_is_null: bool = True,
    ) -> None: 
        stmt = (
            update(rs)
            .where(
                rs.id == rss_source_id,
            )
            .values(
                etag=etag,
                last_modified=last_modified,
            )
        )

        if deleted_is_null:
            stmt = stmt.where(rs.deleted_at.is_(None))

        self._db.execute(stmt)


    def update_news_item_translations(
        self,
        *,
        ids: list[int],
        status: NewsItemTranslationStatus,
        provider: TranslationCode | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        requested_at: datetime | None = None,
        failed_at: datetime | None = None,
        deleted_is_null: bool = True,
    ) -> None: 
        values = {
            "status": status,
        }

        if provider is not None:
            values["provider"] = provider

        if status == NewsItemTranslationStatus.PROCESSING:
            values["requested_at"] = requested_at

        if status == NewsItemTranslationStatus.FAILED:
            values["failed_at"] = failed_at
            values["error_code"] = error_code
            values["error_message"] = error_message

        stmt = (
            update(nit)
            .where(
                and_(
                    nit.id.in_(ids),
                )
            )
            .values(**values)
        )

        if deleted_is_null:
            stmt = stmt.where(nit.deleted_at.is_(None))

        self._db.execute(stmt)

    def update_news_item_translations_done(
        self,
        *,
        rows: list[NewsDTO.NewsItemTranslationDone],
        status: NewsItemTranslationStatus,
        translated_at: datetime,
        deleted_is_null: bool = True,
    ) -> None:
        if not rows:
            return

        for row in rows:
            stmt = (
                update(nit)
                .where(
                    and_(
                        nit.id == row.translation_id,
                        nit.status == NewsItemTranslationStatus.PROCESSING,
                    )
                )
                .values(
                    title=row.title,
                    description=row.description,
                    status=status,
                    translated_at=translated_at,
                    updated_at=translated_at,
                    failed_at=None,
                    error_code=None,
                    error_message=None,
                )
            )

            if deleted_is_null:
                stmt = stmt.where(nit.deleted_at.is_(None))

            self._db.execute(stmt)
