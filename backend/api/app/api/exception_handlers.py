import logging
from typing import Any, cast
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from app.domain import AppError, ConflictError, InternalServerError
from app.api.schema import ErrorSchema

from app.core.settings import settings

log = logging.getLogger(__name__)


def _error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    *,
    target: str | None = None,
    meta: dict[str, Any] | None = None,
):
    body = ErrorSchema.ErrorResponse(
        request_id=request_id,
        error=ErrorSchema.ErrorDetail(code=code, message=message, target=target, meta=meta),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())

def _req_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")

def _log(level: int, msg: str, *, req_id: str, exc: BaseException | None = None, extra: dict | None = None):
    # 운영에선 exc_info 차단(민감정보/스택 노출 방지)
    exc_info = None if settings.DEPLOY_ENV == "prod" else (True if exc else None)
    out_extra = {"request_id": req_id}
    if extra:
        # 운영에서는 민감한 필드 제거/마스킹
        if settings.DEPLOY_ENV == "prod":
            extra = {k: v for k, v in extra.items() if k not in {"db_msg", "params"}}  # 필요시 확장
        out_extra.update(extra)
    log.log(level, msg, exc_info=exc_info, extra=out_extra)

async def unified_exception_handler(request: Request, exc: Exception):
    req_id = _req_id(request)

    # 1) AppError (도메인 에러)
    if isinstance(exc, AppError):
        _log(logging.WARNING, "AppError", req_id=req_id, exc=None, extra={"code": exc.code})
        return _error_response(
            req_id, exc.code, exc.message, exc.status_code, target=exc.target, meta=exc.meta
        )

    # 2) HTTPException (Starlette)
    if isinstance(exc, StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        # 보통 로그는 INFO/NOTICE 수준
        _log(logging.INFO, "HTTPException", req_id=req_id, extra={"status": exc.status_code})
        return _error_response(req_id, "http_error", detail, exc.status_code)

    # 3) Pydantic ValidationError
    if isinstance(exc, RequestValidationError):
        details = [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
        _log(logging.INFO, "ValidationError", req_id=req_id)
        return _error_response(req_id, "validation_error", "Validation failed", 400, meta={"errors": details})

    # 4) DB 무결성 위반
    if isinstance(exc, IntegrityError):
        # 개발/스테이징: 스택 + DB 원문, 운영: 요약만
        db_msg = str(exc.orig) if getattr(exc, "orig", None) else None
        _log(logging.ERROR, "IntegrityError", req_id=req_id, exc=exc, extra={"db_msg": db_msg})
        return _error_response(
            req_id,
            ConflictError.code,
            "Resource conflict",
            409,
            meta={"db": "integrity_error"},
        )

    # 5) 그 외 미처리 예외
    _log(logging.ERROR, "Unhandled error", req_id=req_id, exc=exc)
    return _error_response(
        req_id,
        InternalServerError.code,
        "Internal server error",
        InternalServerError.status_code,
        meta={"type": exc.__class__.__name__},
    )
