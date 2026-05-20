from app.domain import NewsPort, NewsDTO
from app.infra.external.rss.parser import (
    RssFeedParser,
)
from app.infra.external.rss.rest_client import RssRestClient


class NewsFeed(NewsPort.NewsFeed):
    def __init__(
        self,
        *,
        rest_client: RssRestClient,
        parser: RssFeedParser,
    ) -> None:
        self._rest_client = rest_client
        self._parser = parser

    def fetch(self, request: NewsDTO.NewsFeedFetchRequest) -> NewsDTO.NewsFeedFetchResult:
        response = self._rest_client.fetch(
            request.feed_url,
            timeout_sec=request.timeout_sec,
            etag=request.etag,
            last_modified=request.last_modified,
        )

        if response.not_modified:
            return NewsDTO.NewsFeedFetchResult(
                not_modified=True,
                etag=response.etag or request.etag,
                last_modified=response.last_modified or request.last_modified,
                items=[],
            )

        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"rss fetch failed: status_code={response.status_code}")

        if not response.body:
            return NewsDTO.NewsFeedFetchResult(
                not_modified=False,
                etag=response.etag,
                last_modified=response.last_modified,
                items=[],
            )

        parsed = self._parser.parse(response.body)

        return NewsDTO.NewsFeedFetchResult(
            not_modified=False,
            etag=response.etag,
            last_modified=response.last_modified,
            items=parsed.items,
        )