import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from app.domain import AppError, ConflictError, InternalServerError
from app.api.common.envelope import fail, ErrorBody
from app.runtime.settings import settings

from app.core.errors import classify_exception

log = logging.getLogger(__name__)

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

# async def unified_exception_handler(request: Request, exc: Exception):
#     req_id = getattr(request.state, "request_id", "-")
#     info = classify_exception(exc)
#     level = logging.WARNING if (info.http_status and info.http_status < 500) else logging.ERROR

#     _log(level, "APIException", req_id=req_id, extra={
#         "code": info.code,
#         "status": info.http_status or 500,
#         "exc_type": exc.__class__.__name__,
#         "path": request.url.path,
#         "method": request.method,
#     })

#     return fail(
#         ErrorBody(code=info.code, message=info.message, meta={"type": exc.__class__.__name__}),
#         request_id=req_id,
#         status_code=info.http_status or 500,
#     )


async def unified_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "-")

    if isinstance(exc, AppError):
        _log(logging.WARNING, "AppError", req_id=req_id, exc=None, extra={"code": exc.code})
        return fail(
            ErrorBody(code=exc.code, message=exc.message, target=exc.target, meta=exc.meta),
            request_id=req_id, status_code=exc.status_code,
        )

    if isinstance(exc, StarletteHTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        _log(logging.INFO, "HTTPException", req_id=req_id, extra={"status": exc.status_code})
        return fail(ErrorBody(code="http_error", message=detail), request_id=req_id, status_code=exc.status_code)

    if isinstance(exc, RequestValidationError):
        details = [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
        _log(logging.INFO, "ValidationError", req_id=req_id)
        return fail(ErrorBody(code="validation_error", message="Validation failed", meta={"errors": details}),
                    request_id=req_id, status_code=400)

    if isinstance(exc, IntegrityError):
        db_msg = str(exc.orig) if getattr(exc, "orig", None) else None
        _log(logging.ERROR, "IntegrityError", req_id=req_id, exc=exc, extra={"db_msg": db_msg})
        return fail(ErrorBody(code=ConflictError.code, message="Resource conflict", meta={"db":"integrity_error"}),
                    request_id=req_id, status_code=409)
    
    _log(logging.ERROR, "Unhandled error", req_id=req_id, exc=exc)
    return fail(ErrorBody(code=InternalServerError.code, message="Internal server error", meta={"type": exc.__class__.__name__}),
                request_id=req_id, status_code=InternalServerError.status_code)
