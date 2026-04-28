from typing import Protocol, Sequence
from datetime import datetime
from app.domain import NewsDTO

class NewsRepo(Protocol):

    def list_rss_source_by_filter(
        self,
        *,
        is_active: bool = True,
        deleted_is_null: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NewsDTO.RssSource]: ...