from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict

_model_cfg = ConfigDict(from_attributes=True, use_enum_values=True)

class NoticeSimple(BaseModel):
    id: int
    title: str


class NoticeDetailRead(BaseModel):
    model_config = _model_cfg

    id: int
    title: str
    content: str
    category: str
    view_count: int
    summary: str | None = None
    updated_at: datetime | None = None

    prev: NoticeSimple | None = None
    next: NoticeSimple | None = None

class NoticeRead(BaseModel):
    model_config = _model_cfg
    id: int
    title: str
    content: str
    category: str
    view_count: int
    updated_at: datetime | None = None

class FAQRead(BaseModel):
    model_config = _model_cfg
    id: int
    question: str
    answer: str
    category: str
    display_order: int
    updated_at: datetime
