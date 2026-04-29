import logging
from dataclasses import dataclass
from typing import Any, Callable
from app.core.constants import DeploymentEnvironment
from app.core.error.error_model import (
    ErrorSpec,
    from_exception_minimal,
    build_log_fields,
)
from app.core.util.trace import get_trace_id

log = logging.getLogger(__name__)


# --- worker 제어용 예외(핸들러가 던짐) ----------------------------------------


class HandlerError(Exception):
    code = "worker_error"
    severity = "ERROR"
    retryable = False

    def __init__(
        self, message: str, *, target: str | None = None, meta: dict | None = None
    ):
        super().__init__(message)
        self.message = message
        self.target = target
        self.meta = meta or {}


class SkipHandler(HandlerError):
    code = "skipped"
    severity = "INFO"
    retryable = False


class RetryHandler(HandlerError):
    code = "retry"
    severity = "WARNING"
    retryable = True

    def __init__(
        self,
        message: str,
        *,
        target: str | None = None,
        meta: dict | None = None,
    ):
        super().__init__(message, target=target, meta=meta)


class FatalHandler(HandlerError):
    code = "fatal"
    severity = "ERROR"
    retryable = False


class ValidationHandler(HandlerError):
    code = "validation"
    severity = "WARNING"
    retryable = False


# --- deliver_outbox가 쓰기 좋은 결과 -----------------------------------------


@dataclass
class HandlerResult:
    success: bool
    retryable: bool
    result_code: str
    result_message: str | None
    result_payload: dict | None
    spec: ErrorSpec | None = None


# --- 내부: ErrorSpec 만들기 ---------------------------------------------------


def _spec_from_worker_handled(exc: HandlerError) -> ErrorSpec:
    return ErrorSpec(
        code=exc.code,
        message=exc.message,
        status_code=0,
        target=getattr(exc, "target", None),
        meta=getattr(exc, "meta", None),
        exc_type=exc.__class__.__name__,
        stack=None,  # worker는 기본 None 추천 (원하면 include_stack 옵션으로)
        severity=getattr(exc, "severity", "ERROR"),
    )


def _log_spec(
    spec: ErrorSpec,
    *,
    deploy_env: DeploymentEnvironment,
):
    redact_keys = (
        {"db_msg", "params"} if deploy_env == DeploymentEnvironment.PROD else None
    )

    fields = build_log_fields(spec, redact_keys=redact_keys)

    level = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(spec.severity, logging.ERROR)

    # stack을 spec에 넣지 않는 대신, 비PROD면 exc_info로만 남길 수도 있음(선택)
    log.log(level, spec.message, extra=fields)


# --- 퍼블릭 API: dispatch_fn 호출부에서 사용 ----------------------------------


def run_task(
    *,
    deploy_env: DeploymentEnvironment,
    fn: Callable[[], Any],
) -> HandlerResult:
    trace_id = get_trace_id()
    """
    - 핸들러(fn)를 실행하고
    - worker 공통 규약으로 Outcome 생성
    - ErrorSpec 로깅까지 처리
    """
    try:
        result = fn()
        return HandlerResult(
            success=True,
            retryable=False,
            result_code="OK",
            result_message=None,
            result_payload=result,
        )

    except SkipHandler as e:
        spec = _spec_from_worker_handled(e)
        _log_spec(
            spec,
            deploy_env=deploy_env,
        )
        return HandlerResult(
            success=True,
            retryable=False,
            result_code=e.code,
            result_message=e.message,
            result_payload={"skipped": True, "reason": e.message, **(e.meta or {})},
            spec=spec,
        )

    except RetryHandler as e:
        spec = _spec_from_worker_handled(e)
        _log_spec(
            spec,
            deploy_env=deploy_env,
        )
        return HandlerResult(
            success=False,
            retryable=True,
            result_code=e.code,
            result_message=e.message,
            result_payload={"retry": True, "reason": e.message, **(e.meta or {})},
            spec=spec,
        )

    except FatalHandler as e:
        spec = _spec_from_worker_handled(e)
        _log_spec(
            spec,
            deploy_env=deploy_env,
        )
        return HandlerResult(
            success=False,
            retryable=False,
            result_code=e.code,
            result_message=e.message,
            result_payload={"fatal": True, "reason": e.message, **(e.meta or {})},
            spec=spec,
        )

    except Exception as e:
        # 완전 미분류: 기본은 retry 후보로 두는 게 보수적(원하면 False로)
        spec = from_exception_minimal(
            e,
            trace_id=trace_id,
            include_stack=(deploy_env != DeploymentEnvironment.PROD),
        )
        _log_spec(
            spec,
            deploy_env=deploy_env,
        )
        return HandlerResult(
            success=False,
            retryable=False,
            result_code=spec.code,
            result_message=spec.message,
            result_payload=spec.meta if isinstance(spec.meta, dict) else None,
            spec=spec,
        )
