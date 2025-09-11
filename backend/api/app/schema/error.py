from pydantic import BaseModel
from typing import Any, Optional


class ErrorDetail(BaseModel):
    code: str
    message: str
    target: Optional[str] = None
    meta: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    request_id: str
    error: ErrorDetail
