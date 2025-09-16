import logging
from typing import Any, cast
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError

from app.domain import AppError, ConflictError
from app.presentation.schema import ErrorResponse, ErrorDetail

log = logging.getLogger(__name__)


def error_response(
    request_id: str,
    code: str,
    message: str,
    status_code: int,
    *,
    target: str | None = None,
    meta: dict[str, Any] | None = None,
):
    body = ErrorResponse(
        request_id=request_id,
        error=ErrorDetail(code=code, message=message, target=target, meta=meta),
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def handle_app_error(request: Request, exc: Exception):
    app_exc = cast(AppError, exc)  # 또는 assert isinstance(exc, AppError)
    req_id = getattr(request.state, "request_id", "-")
    log.warning("AppError", extra={"request_id": req_id, "code": app_exc.code})
    return error_response(
        req_id,
        app_exc.code,
        app_exc.message,
        app_exc.status_code,
        target=app_exc.target,
        meta=app_exc.meta,
    )


async def handle_http_error(request: Request, exc: Exception):
    http_exc = cast(StarletteHTTPException, exc)
    req_id = getattr(request.state, "request_id", "-")
    detail = http_exc.detail if isinstance(http_exc.detail, str) else "HTTP error"
    return error_response(req_id, "http_error", detail, http_exc.status_code)


async def handle_validation_error(request: Request, exc: Exception):
    val_exc = cast(RequestValidationError, exc)
    req_id = getattr(request.state, "request_id", "-")
    details = [{"loc": e["loc"], "msg": e["msg"]} for e in val_exc.errors()]
    return error_response(
        req_id, "validation_error", "Validation failed", 400, meta={"errors": details}
    )


async def handle_integrity_error(request: Request, exc: Exception):
    integ_exc = cast(IntegrityError, exc)
    req_id = getattr(request.state, "request_id", "-")
    log.warning("IntegrityError", extra={"request_id": req_id})
    return error_response(
        req_id,
        ConflictError.code,
        "Resource conflict",
        409,
        meta={"db": "integrity_error"},
    )
