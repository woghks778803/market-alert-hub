from __future__ import annotations
from typing import Any, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.datetime_utils import utcnow
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import Response, status

T = TypeVar("T")

class Pagination(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)
    has_next: bool

class Meta(BaseModel):
    request_id: str
    timestamp: datetime
    pagination: Pagination | None = None

class ErrorBody(BaseModel):
    code: str
    message: str
    target: str | None = None
    meta: dict[str, Any] | None = None

class Envelope(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorBody | None = None
    meta: Meta

def ok(data: Any, *, request_id: str, pagination: Pagination | None = None) -> Envelope[Any]:
    return Envelope(success=True, data=data, error=None, meta=Meta(request_id=request_id, timestamp=utcnow(), pagination=pagination))

def created(data: Any, *, request_id: str, location: str | None = None):
    """
    201 Created + Envelope 바디 + (선택) Location 헤더
    FastAPI는 (Response-like) 객체를 반환해도 되고, 튜플을 반환해도 됩니다.
    여기서는 JSONResponse로 반환합니다.
    """
    body = ok(data, request_id=request_id)  # success=True envelope 재사용
    headers = {"Location": location} if location else None
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(body),
        headers=headers,
    )

def no_content() -> Response:
    """
    204 No Content는 사양상 바디가 없어야 하므로 Envelope를 쓰지 않고 빈 응답으로 반환.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)

def fail(error: ErrorBody, *, request_id: str, status_code: int, pagination: Pagination | None = None):
    
    body = Envelope(success=False, data=None, error=error, meta=Meta(request_id=request_id, timestamp=utcnow(), pagination=pagination))
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))
