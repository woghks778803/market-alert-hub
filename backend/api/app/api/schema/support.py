from datetime import datetime
from decimal import Decimal

from app.api.schema.base import ApiResponseModel


class NoticeSimple(ApiResponseModel):
    id: int
    title: str


class NoticeDetailRead(ApiResponseModel):
    id: int
    title: str
    content: str
    category: str
    view_count: int
    created_at: datetime
    updated_at: datetime | None = None
    summary: str | None = None

    prev: NoticeSimple | None = None
    next: NoticeSimple | None = None


class NoticeRead(ApiResponseModel):
    id: int
    title: str
    content: str
    category: str
    view_count: int

    created_at: datetime
    updated_at: datetime | None = None


class FAQRead(ApiResponseModel):
    id: int
    question: str
    answer: str
    category: str
    sort_order: int
    updated_at: datetime
