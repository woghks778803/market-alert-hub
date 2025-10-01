import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError
from app.domain import AppError, ConflictError, InternalServerError
from app.api.common.envelope import fail, ErrorBody
from app.core.settings import settings

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

# async def unified_exception_handler(request: Request, exc: Exception):
#     req_id = _req_id(request)

#     # 1) AppError (도메인 에러)
#     if isinstance(exc, AppError):
#         _log(logging.WARNING, "AppError", req_id=req_id, exc=None, extra={"code": exc.code})
#         return _error_response(
#             req_id, exc.code, exc.message, exc.status_code, target=exc.target, meta=exc.meta
#         )

#     # 2) HTTPException (Starlette)
#     if isinstance(exc, StarletteHTTPException):
#         detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
#         # 보통 로그는 INFO/NOTICE 수준
#         _log(logging.INFO, "HTTPException", req_id=req_id, extra={"status": exc.status_code})
#         return _error_response(req_id, "http_error", detail, exc.status_code)

#     # 3) Pydantic ValidationError
#     if isinstance(exc, RequestValidationError):
#         details = [{"loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
#         _log(logging.INFO, "ValidationError", req_id=req_id)
#         return _error_response(req_id, "validation_error", "Validation failed", 400, meta={"errors": details})

#     # 4) DB 무결성 위반
#     if isinstance(exc, IntegrityError):
#         # 개발/스테이징: 스택 + DB 원문, 운영: 요약만
#         db_msg = str(exc.orig) if getattr(exc, "orig", None) else None
#         _log(logging.ERROR, "IntegrityError", req_id=req_id, exc=exc, extra={"db_msg": db_msg})
#         return _error_response(
#             req_id,
#             ConflictError.code,
#             "Resource conflict",
#             409,
#             meta={"db": "integrity_error"},
#         )

#     # 5) 그 외 미처리 예외
#     _log(logging.ERROR, "Unhandled error", req_id=req_id, exc=exc)
#     return _error_response(
#         req_id,
#         InternalServerError.code,
#         "Internal server error",
#         InternalServerError.status_code,
#         meta={"type": exc.__class__.__name__},
#     )
