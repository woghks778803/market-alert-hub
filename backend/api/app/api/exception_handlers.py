import logging
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import IntegrityError

from app.core.error.error_model import (
    ErrorSpec,
    from_exception_minimal,
    build_log_fields,
)
from app.domain.shared.errors import AppError
from app.api.deps import api_config
from app.api.common.envelope import fail, ErrorBody

log = logging.getLogger(__name__)


def _spec_from_request_validation_error(
    exc: RequestValidationError, req_id: str
) -> ErrorSpec:
    # FastAPI의 validation error → 무조건 클라이언트 잘못으로 보고 400
    details: list[dict[str, object]] = []
    try:
        for e in exc.errors():
            if isinstance(e, dict):
                details.append({"loc": e.get("loc"), "msg": e.get("msg")})
    except Exception:
        # 방어적으로. parsing 실패해도 전체 핸들러가 죽으면 안 되니까.
        pass

    return ErrorSpec(
        code="validation_error",
        message="Validation failed",
        status_code=400,
        target=None,
        meta={"errors": details} if details else None,
        trace_id=req_id,
        exc_type=exc.__class__.__name__,
        stack=None,  # validation은 비즈니스 레벨에서 충분히 설명 가능한 오류라 stack은 필요 없음
        severity="INFO",
    )


def _spec_from_http_exception(exc: StarletteHTTPException, req_id: str) -> ErrorSpec:
    # Starlette/FastAPI HTTPException류 → 그대로 노출해도 된다고 가정
    detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"

    severity = "INFO" if exc.status_code < 500 else "ERROR"

    return ErrorSpec(
        code="http_error",
        message=detail,
        status_code=exc.status_code,
        target=None,
        meta=None,
        trace_id=req_id,
        exc_type=exc.__class__.__name__,
        stack=None,  # HTTPException은 의도적 리턴 케이스가 많음 -> stack 굳이 X
        severity=severity,
    )


def _spec_from_integrity_error(exc: IntegrityError, req_id: str) -> ErrorSpec:
    # DB unique 제약 등 충돌 상황 → API에선 409 Conflict로 응답
    # (worker에서는 다르게 처리할 수 있음. 그건 worker 래퍼에서 별도 분기)
    db_msg = None
    if getattr(exc, "orig", None) is not None:
        try:
            db_msg = str(exc.orig)
        except Exception:
            pass

    return ErrorSpec(
        code="conflict",
        message="Resource conflict",
        status_code=409,
        target=None,
        meta={
            "db": "integrity_error",
            "db_msg": db_msg,
        },
        trace_id=req_id,
        exc_type=exc.__class__.__name__,
        # IntegrityError는 운영 이슈일 수도 있어서 비프로덕션에선 stack 기록해두자
        stack=None if api_config.deploy_env == "prod" else "IntegrityError",
        severity="ERROR",
    )


def _to_public_error_body(spec: ErrorSpec) -> ErrorBody:
    """
    API 응답 바디(Envelope.fail에 들어가는 ErrorBody)로 변환.
    ErrorSpec은 좀 더 내부/로깅 친화적 모델이라, API에선 필요한 필드만 노출.
    """
    return ErrorBody(
        code=spec.code,
        message=spec.message,
        target=spec.target,
        meta=spec.meta,
    )


async def unified_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "-")

    # 1) 예외 타입을 API 맥락에서 해석해 ErrorSpec으로 변환
    if isinstance(exc, RequestValidationError):
        spec = _spec_from_request_validation_error(exc, req_id)

    elif isinstance(exc, StarletteHTTPException):
        spec = _spec_from_http_exception(exc, req_id)

    elif isinstance(exc, IntegrityError):
        spec = _spec_from_integrity_error(exc, req_id)

    elif isinstance(exc, AppError):
        # AppError는 도메인 규칙 위반(비즈니스 에러)이므로 core 쪽 최소 정규화랑 동일한 의미
        # 여기선 include_stack=False로 두는 게 자연스럽다 (의도적으로 raise한 에러라 stack까지 굳이 X)
        spec = from_exception_minimal(
            exc,
            trace_id=req_id,
            include_stack=False,
        )
        # from_exception_minimal은 AppError면 WARNING / status_code는 AppError.status_code 유지
        # 그대로 쓰면 된다.

    else:
        # 완전 예기치 않은 예외 → 내부 서버 에러로 처리
        # 이건 운영 디버깅을 위해 prod가 아니면 stack 포함시켜도 된다.
        spec = from_exception_minimal(
            exc,
            trace_id=req_id,
            include_stack=(api_config.deploy_env != "prod"),
        )

    # 2) 로그 남기기
    # 민감 키 마스킹: prod에서는 db_msg, params 같은 내부 구현 세부는 버린다.
    redact_keys = {"db_msg", "params"} if api_config.deploy_env == "prod" else None

    log_fields = build_log_fields(
        spec,
        ctx={
            "path": str(request.url.path),
            "method": request.method,
        },
        redact_keys=redact_keys,
    )

    # 로그 레벨 매핑
    log_level = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(spec.severity, logging.ERROR)

    log.log(
        log_level,
        "request_error",
        extra={"request_id": req_id, **log_fields},
        exc_info=(None if api_config.deploy_env == "prod" else True),
    )

    # 3) 외부로 노출할 형태로 마스킹
    public_spec = spec.mask_internal(should_mask=(api_config.deploy_env == "prod"))
    # 4) Envelope.fail() 조립해서 FastAPI Response 리턴
    return fail(
        _to_public_error_body(public_spec),
        request_id=req_id,
        status_code=public_spec.status_code,
    )
