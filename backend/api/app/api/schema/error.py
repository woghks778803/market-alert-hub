from pydantic import BaseModel
from typing import Any


class ErrorDetail(BaseModel):
    code: str
    message: str
    target: str | None = None
    meta: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    request_id: str
    error: ErrorDetail
