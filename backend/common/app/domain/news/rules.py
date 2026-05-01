import json
import base64
from datetime import datetime
from app.core.constants import NewsPostsort
import app.domain.news.dto as NewsDTO

def decode_news_post_cursor(cursor: str) -> NewsDTO.NewsPostListCursor:
    raw = base64.urlsafe_b64decode(cursor.encode()).decode()
    payload = json.loads(raw)

    return NewsDTO.NewsPostListCursor(
        sort=NewsPostsort(payload["sort"]),
        news_item_id=int(payload["news_item_id"]),
        cursor_at=(
            datetime.fromisoformat(payload["cursor_at"])
            if payload.get("cursor_at")
            else None
        ),
    )

def make_news_post_cursor(*, sort: NewsPostsort, item) -> str:
    cursor_at = item.published_at if item.published_at else item.fetched_at

    payload = {
        "sort": sort.value,
        "news_item_id": item.news_item_id,
        "cursor_at": cursor_at.isoformat(),
    }

    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()