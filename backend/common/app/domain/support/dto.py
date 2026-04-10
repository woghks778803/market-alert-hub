from dataclasses import dataclass
from datetime import datetime
from app.core.constants import NoticeCategory, FAQCategory

@dataclass(slots=True)
class Notice:
    id: int
    title: str
    content: str
    category: NoticeCategory
    view_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

@dataclass(slots=True)
class NoticeSimple:
    id: int
    title: str

@dataclass(slots=True)
class NoticeDetail:
    id: int
    title: str
    content: str
    category: str
    is_active: bool
    view_count: int
    created_at: datetime
    updated_at: datetime

    summary: str | None
    prev: NoticeSimple | None
    next: NoticeSimple | None

@dataclass(slots=True)
class FAQ:
    id: int
    question: str
    answer: str
    category: FAQCategory
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime