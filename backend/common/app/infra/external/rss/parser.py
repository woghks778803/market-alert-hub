import re
import feedparser
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from time import struct_time

from app.core.constants import LanguageCode

@dataclass(frozen=True)
class ParsedNewsFeedItem:
    guid: str | None
    link: str | None
    title: str | None
    description: str | None
    content: str | None
    author: str | None
    image_url: str | None
    published_at: datetime | None


@dataclass(frozen=True)
class ParsedNewsFeed:
    title: str | None
    language: str | None
    items: list[ParsedNewsFeedItem]


class RssFeedParser:
    def parse(self, xml_text: str) -> ParsedNewsFeed:
        feed = feedparser.parse(xml_text)

        items = [
            self._to_item(entry)
            for entry in feed.entries
        ]

        return ParsedNewsFeed(
            title=self._clean_text(feed.feed.get("title")),
            language=self._normalize_language(feed.feed.get("language")),
            items=items,
        )

    def _to_item(self, entry) -> ParsedNewsFeedItem:
        return ParsedNewsFeedItem(
            guid=self._get_guid(entry),
            link=self._clean_text(entry.get("link")),
            title=self._clean_text(entry.get("title")),
            description=self._get_description(entry),
            content=self._get_content(entry),
            author=self._clean_text(
                entry.get("author")
                or entry.get("creator")
                or entry.get("dc_creator")
            ),
            image_url=self._get_image_url(entry),
            published_at=self._get_published_at(entry),
        )

    def _get_guid(self, entry) -> str | None:
        value = (
            entry.get("id")
            or entry.get("guid")
            or entry.get("link")
        )

        return self._clean_text(value)

    def _get_description(self, entry) -> str | None:
        value = (
            entry.get("summary")
            or entry.get("description")
            or entry.get("subtitle")
        )

        return self._clean_html(value)

    def _get_content(self, entry) -> str | None:
        contents = entry.get("content")

        if not contents:
            return None

        first = contents[0]

        if isinstance(first, dict):
            return self._clean_html(first.get("value"))

        return self._clean_html(str(first))

    def _get_image_url(self, entry) -> str | None:
        media_thumbnail = entry.get("media_thumbnail")
        if media_thumbnail:
            first = media_thumbnail[0]
            if isinstance(first, dict) and first.get("url"):
                return first["url"]

        media_content = entry.get("media_content")
        if media_content:
            for item in media_content:
                if not isinstance(item, dict):
                    continue

                url = item.get("url")
                mime_type = item.get("type", "")

                if url and mime_type.startswith("image/"):
                    return url

            first = media_content[0]
            if isinstance(first, dict) and first.get("url"):
                return first["url"]

        links = entry.get("links")
        if links:
            for link in links:
                if not isinstance(link, dict):
                    continue

                href = link.get("href")
                mime_type = link.get("type", "")

                if href and mime_type.startswith("image/"):
                    return href

        return None

    def _get_published_at(self, entry) -> datetime | None:
        parsed = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
            or entry.get("created_parsed")
        )

        if isinstance(parsed, struct_time):
            return datetime(*parsed[:6], tzinfo=timezone.utc)

        value = (
            entry.get("published")
            or entry.get("updated")
            or entry.get("created")
        )

        if not value:
            return None

        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    def _clean_text(self, value: str | None) -> str | None:
        if not value:
            return None

        text = unescape(str(value))
        text = re.sub(r"\s+", " ", text)

        return text.strip() or None

    def _clean_html(self, value: str | None) -> str | None:
        if not value:
            return None

        text = unescape(str(value))
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text)

        return text.strip() or None

    def _normalize_language(self, value: str | None) -> str | None:
        if not value:
            return None

        normalized = value.strip().lower()

        if normalized.startswith(LanguageCode.EN.value):
            return LanguageCode.EN.value
        if normalized.startswith(LanguageCode.KO.value):
            return LanguageCode.KO.value
        if normalized.startswith(LanguageCode.JA.value):
            return LanguageCode.JA.value
        if normalized.startswith(LanguageCode.ZH.value):
            return LanguageCode.ZH.value

        return normalized