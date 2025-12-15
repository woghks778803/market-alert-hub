import logging
from typing import Callable, Any
from sqlalchemy.exc import IntegrityError

from common.core.error.error_model import (
    ErrorSpec,
    from_exception_minimal,
    build_log_fields,
)
from app.domain import AppError  # 도메인에서 선언한 AppError 계열 가정
from app.runtime.settings import settings  # worker도 DEPLOY_ENV, etc 쓸 수 있다고 가정

log = logging.getLogger(__name__)


def _spec_from_integrity_error_for_worker(
    exc: IntegrityError, job_id: str
) -> ErrorSpec:
    """
    Worker 관점에서 IntegrityError는 보통 '이미 처리된 이벤트' / '중복 삽입 차단'처럼
    멱등성 확보 시나리오일 가능성이 높다.
    즉, 이건 시스템 폭발이 아니라 '재시도 불필요한 정상적 중복'일 수도 있다.

    여기서는 기본적으로 WARNING (혹은 INFO도 가능)로 보고 retry 불필요하게 취급한다.
    상태코드는 409 (충돌) 같은 걸 재사용해도 된다. HTTP 의미로 쓰는 건 아니고,
    '이건 논리적으로 충돌 난 거라서 재시도해도 안 바뀐다'라는 시그널로 쓰는 거다.
    """
    db_msg = None
    if getattr(exc, "orig", None) is not None:
        try:
            db_msg = str(exc.orig)
        except Exception:
            pass

    return ErrorSpec(
        code="conflict",
        message="Idempotent conflict",
        status_code=409,
        target=None,
        meta={
            "db": "integrity_error",
            "db_msg": db_msg,
        },
        trace_id=job_id,
        exc_type=exc.__class__.__name__,
        # worker 로그는 내부 전용이라 비프로덕션 여부랑 상관없이 stack을 굳이 넣지 않아도 됨.
        # 필요하면 여기서 include_stack 제어 가능
        stack=None,
        severity="WARNING",
    )


def _spec_from_app_error_for_worker(exc: AppError, job_id: str) -> ErrorSpec:
    """
    비즈니스 규칙 에러(AppError)는 '요청 자체가 비즈니스적으로 실패했다'에 가깝다.
    보통 retry해도 해결 안 됨. 그러니까 retry_stop 쪽으로 보내고 알림은 WARNING 정도로 충분.
    """
    return ErrorSpec(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        target=getattr(exc, "target", None),
        meta=getattr(exc, "meta", None),
        trace_id=job_id,
        exc_type=exc.__class__.__name__,
        stack=None,  # 의도적으로 raise된 도메인 에러라 stack은 크게 의미 없음
        severity="WARNING",
    )


def _spec_from_unhandled_for_worker(exc: Exception, job_id: str) -> ErrorSpec:
    """
    완전히 예기치 않은 런타임 에러.
    이건 인프라나 코드 버그일 수 있어서 retry 후보로 봐야 할 가능성이 높다.
    -> severity="ERROR"
    -> status_code=500 등
    여기서는 core의 from_exception_minimal을 재사용하되,
    include_stack은 prod 여부 따라 제어할 수 있다.
    """
    return from_exception_minimal(
        exc,
        trace_id=job_id,
        include_stack=(settings.DEPLOY_ENV != "prod"),
    )


def _log_spec(spec: ErrorSpec, job_name: str):
    """
    ErrorSpec 기반으로 worker 로그 남기기.
    API랑 거의 같지만, worker 관점의 ctx를 넣는다.
    """
    # prod에선 민감한 db_msg 같은 거 빼자
    redact_keys = {"db_msg", "params"} if settings.DEPLOY_ENV == "prod" else None

    log_fields = build_log_fields(
        spec,
        ctx={"job": job_name},
        redact_keys=redact_keys,
    )

    level = {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }.get(spec.severity, logging.ERROR)

    log.log(
        level,
        "worker_job_error",
        extra={"job_id": spec.trace_id, **log_fields},
        exc_info=(None if settings.DEPLOY_ENV == "prod" else True),
    )


class JobResult:
    """
    worker 실행 결과를 래핑해서 호출자가 후속 행동(retry, DLQ 등)을 쉽게 결정할 수 있게 돕는 구조.

    success: 잡이 예외 없이 끝났는지
    spec: 실패 시 ErrorSpec (성공이면 None)
    retryable: 재시도할 가치가 있는지 (운영 정책 결정 포인트)
    """

    def __init__(self, success: bool, spec: ErrorSpec | None, retryable: bool):
        self.success = success
        self.spec = spec
        self.retryable = retryable


def run_job(job_name: str, job_id: str, job_func: Callable[[], Any]) -> JobResult:
    """
    개별 잡 실행 래퍼.

    job_name: 작업 타입/태그 (ex: "send_outbox", "reconcile_accounting")
    job_id: 이 작업 실행 단위의 식별자 (trace_id로도 쓴다)
    job_func: 실제 작업 로직(예외 날릴 수 있음)

    반환값으로 JobResult를 돌려줘서 호출 측(큐 컨슈머 루프나 스케줄러)이
    retry / DLQ / ack 등의 결정을 할 수 있게 한다.
    """

    try:
        job_func()
        # 성공
        return JobResult(success=True, spec=None, retryable=False)

    except IntegrityError as e:
        # 멱등 충돌 같은 케이스 -> 보통 재시도 불필요
        spec = _spec_from_integrity_error_for_worker(e, job_id)
        _log_spec(spec, job_name)
        return JobResult(success=False, spec=spec, retryable=False)

    except AppError as e:
        # 비즈니스 에러 -> 보통 재시도해도 안 바뀜
        spec = _spec_from_app_error_for_worker(e, job_id)
        _log_spec(spec, job_name)
        return JobResult(success=False, spec=spec, retryable=False)

    except Exception as e:
        # 진짜 알 수 없는 에러 -> retryable=True 로 보내서 상위 레이어에서 재시도 판단
        spec = _spec_from_unhandled_for_worker(e, job_id)
        _log_spec(spec, job_name)
        return JobResult(success=False, spec=spec, retryable=True)
