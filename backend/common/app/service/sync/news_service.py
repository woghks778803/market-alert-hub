from typing import Callable, Any
import logging
from datetime import datetime

from app.core import dto as CoreDTO
from app.core.constants import (
    TranslationCode, 
    LanguageCode, 
    NewsItemStatus, 
    NewsItemTranslationStatus, 
    OutboxStatus, 
    OutboxEventType
)

from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.core.util.text import normalize_spaces, normalize_nullable_text
from app.core.util.url import canonicalize_url

from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import InternalServerError, ValidationAppError
from app.domain import NewsPort, NewsDTO, CryptoPort, OutboxDTO

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        google_translation: NewsPort.GoogleTranslation,
        news_feed: NewsPort.NewsFeed,
        hmac: CryptoPort.TokenHasher,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_translation = google_translation
        self._news_feed = news_feed
        self._hmac = hmac

    def list_news_feed_by_filter(
        self, 
        *, 
        limit: int = 100,
        offset: int = 0,
    ):
        with self._uow_factory() as uow:
            return uow.newses.list_news_feed_by_filter(limit=limit, offset=offset)

    def fetch_news_feed(
        self,
        *,
        slot: int,
        rss_source_id: int,
        rss_source_code: str,
        batch_size: int,
    ) -> dict: 
        # print("fetch_news_feed", slot, rss_source_id, rss_source_code, batch_size)
        now = utcnow()
        trace_id = get_trace_id()

        with self._uow_factory() as uow:
            # rss source 검색
            news_feed = uow.newses.get_news_feed_by_id(rss_source_id=rss_source_id)

            # news_feed 데이터 가져오기
            result: NewsDTO.NewsFeedFetchResult = self._news_feed.fetch(
                request=NewsDTO.NewsFeedFetchRequest(
                    feed_url=news_feed.feed_url,
                    timeout_sec=news_feed.request_timeout_sec,
                    etag=news_feed.etag,
                    last_modified=news_feed.last_modified,
                )
            )

            if result.not_modified:
                return {
                    "slot": slot,
                    "rss_source_id": rss_source_id,
                    "rss_source_code": rss_source_code,
                    "not_modified": True,
                    "fetched_news_item_count": 0,
                    "processed_news_item_count": 0,
                    "created_news_item_count": 0,
                }

            # print("fetch_news_feed result", result)
            items = result.items[:batch_size] # 전부 가져올 필요없음

            news_items: list[NewsDTO.NewsItemCreate] = []

            for item in items:
                if not item.title or not item.link:
                    continue

                title_original = normalize_spaces(item.title)
                canonical_link = canonicalize_url(item.link)

                description_original = (
                    normalize_nullable_text(item.description)
                    if item.description
                    else None
                )
                content_original = (
                    normalize_nullable_text(item.content)
                    if item.content
                    else None
                )

                content_source = content_original or description_original

                news_items.append(
                    NewsDTO.NewsItemCreate(
                        rss_source_id=news_feed.rss_source_id,
                        guid=item.guid,
                        link=item.link,
                        canonical_link=canonical_link,
                        title_original=item.title,
                        description_original=description_original,
                        content_original=content_original,
                        image_url=item.image_url,
                        author=item.author,
                        language=news_feed.language,
                        published_at=item.published_at,
                        fetched_at=now,
                        title_fingerprint=self._hmac.fp_hash(title_original),
                        link_fingerprint=self._hmac.fp_hash(canonical_link),
                        content_fingerprint=(
                            self._hmac.fp_hash(content_source)
                            if content_source
                            else None
                        ),
                        status=NewsItemStatus.ACTIVE,
                    )
                )

            existing_news_items = uow.newses.list_news_item_by_link_fingerprints(
                rss_source_id=news_feed.rss_source_id,
                link_fingerprints=[item.link_fingerprint for item in news_items],
            )

            existing_fps = [item.link_fingerprint for item in existing_news_items]
            existing_fp_set = set(existing_fps)

            created_candidates = [
                item
                for item in news_items
                if item.link_fingerprint not in existing_fp_set
            ]

            uow.newses.upsert_news_items(rows=news_items)

            created_news_items = uow.newses.list_news_item_by_link_fingerprints(
                rss_source_id=news_feed.rss_source_id,
                link_fingerprints=[item.link_fingerprint for item in created_candidates],
            )

            # print("created_news_items", created_news_items)

            # 새로 들어간 item만 news_item_translations PENDING 생성
            created_stat_count = 0
            created_translation_count = 0
            if created_news_items:
                uow.newses.add_news_item_stats(
                    rows=[
                        NewsDTO.NewsItemStatCreate(
                            news_item_id=item.id,
                            click_count=0,
                            share_count=0,
                            last_clicked_at=None,
                        )
                        for item in created_news_items
                    ],
                )

                uow.newses.add_news_item_translations(
                    rows=[
                        NewsDTO.NewsItemTranslationCreate(
                            news_item_id=item.id,
                            locale=LanguageCode.KO,
                            status=NewsItemTranslationStatus.PENDING,
                        )
                        for item in created_news_items
                    ],
                )

            # rss_sources etag / last_modified 갱신
            uow.newses.update_rss_source(
                rss_source_id=news_feed.rss_source_id,
                etag=result.etag,
                last_modified=result.last_modified,
            )

            # 번역 outbox 생성
            fp_dict: dict[str, Any] = {
                "event_type": OutboxEventType.TRANSLATE_NEWS_ITEMS.value,
                "aggregate_type": "rss_source",
                "aggregate_id": rss_source_id,
                "slot": slot,
            }

            outbox_fingerprint = to_canonical_json(fp_dict)
            outbox_fingerprint = (
                self._hmac.fp_hash(outbox_fingerprint)
                if outbox_fingerprint is not None
                else None
            )

            # 4) outbox enqueue
            uow.outboxs.add_outbox(
                OutboxDTO.OutboxCreate(
                    trace_id=trace_id,
                    event_type=OutboxEventType.TRANSLATE_NEWS_ITEMS,
                    aggregate_type="rss_source",
                    aggregate_id=rss_source_id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload={
                        "rss_source_id": rss_source_id,
                        "rss_source_code": rss_source_code,
                        "locale": LanguageCode.KO.value,
                        "slot": slot,
                    },
                    status=OutboxStatus.PENDING,
                    attempts=0,
                ),
                True,
            )

            uow.commit()

            return {
                "slot": slot,
                "rss_source_id": rss_source_id,
                "rss_source_code": rss_source_code,
                "not_modified": False,
                "fetched_news_item_count": len(items),
                "processed_news_item_count": len(news_items),
                "created_news_item_count": len(created_news_items),
            }

    def translate_news_items(
        self,
        *,
        rss_source_id: int,
        rss_source_code: str,
        locale: LanguageCode,
        batch_size: int,
    ) -> dict: 
        now = utcnow()
        # print("translate_news_items", rss_source_id, rss_source_code, locale, batch_size)

        with self._uow_factory() as uow:
            # pending translate list
            targets = uow.newses.list_news_item_translation_by_filter(
                rss_source_id=rss_source_id,
                locale=LanguageCode.KO,
                translation_status=NewsItemTranslationStatus.PENDING,
                item_status=NewsItemStatus.ACTIVE,
            )

            # print("translate_news_items targets", targets)

            if not targets:
                return {
                    "rss_source_id": rss_source_id,
                    "rss_source_code": rss_source_code,
                    "locale": locale.value,
                    "target_count": 0,
                    "translated_count": 0,
                    "failed_count": 0,
                }
            
        translated_count = 0
        failed_count = 0

        for i in range(0, len(targets), batch_size):
            chunk = targets[i: i + batch_size]
            chunk_ids = [x.translation_id for x in chunk]

            if not chunk_ids:
                continue

            # update processing translate
            with self._uow_factory() as uow:
                uow.newses.update_news_item_translations(
                    ids=chunk_ids,
                    provider=TranslationCode.GOOGLE,
                    status=NewsItemTranslationStatus.PROCESSING,
                    requested_at=utcnow()
                )
                uow.commit()

            try:
                done_rows = self._translate_news_item_chunk(
                    targets=chunk,
                    locale=locale,
                )

                # print("done_rows", done_rows)

                with self._uow_factory() as uow:
                    uow.newses.update_news_item_translations_done(
                        rows=done_rows,
                        status=NewsItemTranslationStatus.DONE,
                        translated_at=utcnow()
                    )
                    uow.commit()

                translated_count += len(done_rows)
                
            except Exception as e:
                # print("translate_news_items Exception", e)
                with self._uow_factory() as uow:
                    uow.newses.update_news_item_translations(
                        ids=chunk_ids,
                        error_code=type(e).__name__,
                        error_message=str(e),
                        status=NewsItemTranslationStatus.FAILED,
                        failed_at=utcnow()
                    )
                    uow.commit()

                failed_count += len(chunk_ids)

        return {
            "rss_source_id": rss_source_id,
            "rss_source_code": rss_source_code,
            "locale": locale.value,
            "target_count": len(targets),
            "translated_count": translated_count,
            "failed_count": failed_count,
        }

    def _translate_news_item_chunk(
        self,
        *,
        targets: list[NewsDTO.NewsItemTranslationTarget],
        locale: LanguageCode,
    ) -> list[NewsDTO.NewsItemTranslationDone]:
        targets_by_language: dict[LanguageCode, list[NewsDTO.NewsItemTranslationTarget]] = {}

        for target in targets:
            source_language = LanguageCode.UNKNOWN
            if target.item_language != LanguageCode.UNKNOWN:
                source_language = target.item_language
            elif target.provider_language != LanguageCode.UNKNOWN:
                source_language = target.provider_language
            
            targets_by_language.setdefault(source_language, []).append(target)
        
        mapped: dict[int, dict[str, str | None]] = {
            target.translation_id: {
                "title": None,
                "description": None,
            }
            for target in targets
        }

        for idx, values in targets_by_language.items():
            # print("translation_targets", idx, values)

            title_items = [
                NewsDTO.TranslateTextItem(
                    ref_id=value.translation_id,
                    text=value.title_original,
                )
                for value in values
                if value.title_original
            ]

            # print("title_items", title_items)

            if title_items:
                title_results = self._google_translation.translate_batch(
                    request=NewsDTO.TranslateBatchRequest(
                        source_language=source_language if source_language != LanguageCode.UNKNOWN else None,
                        target_language=locale,
                        items=title_items,
                    )
                )

                # print("title_results", title_results)

                for item in title_results.items:
                    mapped[item.ref_id]["title"] = item.translated_text

            # TODO: 번역 사용량을 늘릴때 적용
            # description_items = [
            #     NewsDTO.TranslateTextItem(
            #         ref_id=value.translation_id,
            #         text=value.description_original,
            #     )
            #     for value in values
            #     if value.description_original
            # ]
    
            # if description_items:
            #     description_result = self._google_translation.translate_batch(
            #         request=NewsDTO.TranslateBatchRequest(
            #             source_language=source_language if source_language != LanguageCode.UNKNOWN else None,
            #             target_language=locale,
            #             items=description_items,
            #         )
            #     )

            #     for item in description_result.items:
            #         mapped[item.ref_id]["description"] = item.translated_text

        # print("mapped NewsItemTranslationDone", mapped)
        return [
            NewsDTO.NewsItemTranslationDone(
                translation_id=translation_id,
                title=values["title"],
                description=values["description"],
            )
            for translation_id, values in mapped.items()
        ]

