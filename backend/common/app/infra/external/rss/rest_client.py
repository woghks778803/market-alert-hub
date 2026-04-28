from dataclasses import dataclass
from urllib.parse import urlsplit

from app.infra.external.transport.impl.httpx import (
    HttpxTransport,
    HttpxTransportConfig,
)
from app.infra.external.transport.port.http import SyncHttpTransport


@dataclass(frozen=True)
class RssRequestConfig:
    user_agent: str = "market-alert-hub-rss/1.0"


@dataclass(frozen=True)
class RssFetchResponse:
    status_code: int
    body: str | None
    etag: str | None
    last_modified: str | None
    not_modified: bool


class RssRestClient:
    def __init__(self, config: RssRequestConfig) -> None:
        self._config = config

    def fetch(
        self,
        feed_url: str,
        *,
        timeout_sec: float,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> RssFetchResponse:
        base_url, path = self._split_url(feed_url)

        transport = HttpxTransport(
            HttpxTransportConfig(
                base_url=base_url,
                timeout_sec=timeout_sec,
            )
        )

        headers = {
            "User-Agent": self._config.user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        }

        if etag:
            headers["If-None-Match"] = etag

        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            response = transport.get(path, headers=headers)
        finally:
            transport.close()

        status_code = self._status_code(response)

        return RssFetchResponse(
            status_code=status_code,
            body=None if status_code == 304 else self._body(response),
            etag=self._header(response, "etag"),
            last_modified=self._header(response, "last-modified"),
            not_modified=status_code == 304,
        )

    def _split_url(self, url: str) -> tuple[str, str]:
        parsed = urlsplit(url)

        if not parsed.scheme or not parsed.netloc:
            raise ValueError("invalid rss feed url")

        base_url = f"{parsed.scheme}://{parsed.netloc}"
        path = parsed.path or "/"

        if parsed.query:
            path = f"{path}?{parsed.query}"

        return base_url, path

    def _status_code(self, response) -> int:
        return getattr(response, "status_code", 0)

    def _body(self, response) -> str:
        text = getattr(response, "text", None)
        if text is not None:
            return text

        body = getattr(response, "body", None)
        if isinstance(body, bytes):
            return body.decode("utf-8", errors="replace")

        if body is not None:
            return str(body)

        return ""

    def _header(self, response, key: str) -> str | None:
        headers = getattr(response, "headers", None)
        if not headers:
            return None

        return (
            headers.get(key)
            or headers.get(key.lower())
            or headers.get(key.upper())
        )


def get_rss_rest_client(
    config: RssRequestConfig
) -> RssRestClient:
    return RssRestClient(config)