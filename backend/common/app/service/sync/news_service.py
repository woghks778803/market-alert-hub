from typing import Callable, Any
import logging
from datetime import datetime

from app.core import dto as CoreDTO
from app.core.constants import OutboxStatus, OutboxEventType
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import InternalServerError, ValidationAppError
from app.domain import NewsPort

logger = logging.getLogger(__name__)


class NewsService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        google_translation: NewsPort.GoogleTranslation,
        news_feed: NewsPort.NewsFeed,
    ) -> None:
        self._uow_factory = uow_factory
        self._google_translation = google_translation
        self._news_feed = news_feed

    def list_rss_source_by_filter(
        self, 
        *, 
        limit: int = 100,
        offset: int = 0,
    ):
        with self._uow_factory() as uow:
            return uow.newses.list_rss_source_by_filter(limit=limit, offset=offset)