from typing import Protocol
import app.domain.news.dto as NewsDTO

class NewsFeed(Protocol):
    def fetch(
        self, 
        request: NewsDTO.NewsFeedFetchRequest
    ) -> NewsDTO.NewsFeedFetchResult:
        raise NotImplementedError

class GoogleTranslation:
    def translate_batch(
        self,
        request: NewsDTO.TranslateBatchRequest,
    ) -> NewsDTO.TranslateBatchResult:
        raise NotImplementedError

    