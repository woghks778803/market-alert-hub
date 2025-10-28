from dataclasses import dataclass
from typing import Any, Optional, Dict, Literal
import traceback


@dataclass
class ErrorSpec:
    """
    서비스 간 공통으로 사용하는 에러 표현 포맷.

    - code: 비즈니스/분류 코드 (예: "validation_error", "conflict", "USER_NOT_FOUND", "internal_error")
    - message: 사람에게 보여줄 메시지 (서비스별로 마스킹 전/후 다를 수 있음)
    - status_code: 의미상의 심각도/등급. API는 이걸 HTTP status로도 재사용할 수 있고,
                   워커는 retry 여부 판단 기준으로 써도 된다.
                   즉 "HTTP 전용" 아님. 그냥 '이 에러는 어느 레벨인가'를 숫자로 나타낸 공통 슬롯.
    - target: 어떤 리소스/필드/엔티티에 대한 에러인지 (없으면 None)
    - meta: 부가 정보(디버깅, context). 민감할 수 있으므로 서비스 레이어에서 마스킹 책임을 짐.

    추가 필드(운영/관측용):
    - trace_id: 요청/작업 단위 식별자. API면 request_id, 워커면 job_id 등.
    - exc_type: 실제 발생한 예외 클래스명 (ex: "ValueError", "UserNotFoundError")
    - stack: 스택 트레이스(비프로덕션에서만 보존 가능). prod에선 None으로 날리는 걸 권장.
    - severity: "INFO" | "WARNING" | "ERROR"
                -> 서비스가 로그 레벨/알람 임계점 결정할 때 사용.
    """

    code: str
    message: str
    status_code: int
    target: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    trace_id: str = "-"
    exc_type: str = "Exception"
    stack: Optional[str] = None
    severity: Literal["INFO", "WARNING", "ERROR"] = "ERROR"

    def mask_internal(self, *, should_mask: bool) -> "ErrorSpec":
        """
        민감 정보/내부 디버깅 정보를 외부로 내보내기 전에 가리는 용도.
        서비스 레이어(API, worker 등)가 '이 상황은 마스킹해야 한다'라고 판단하면
        should_mask=True로 호출한다.

        현재 공통 규칙:
        - 5xx 급(status_code 500~599)은 외부로 나갈 때 상세 내용을 숨긴다.
        - 그 외 코드는 그대로 둔다.

        중요한 점:
        - core은 환경("prod") 같은 걸 모른다.
        즉 prod인지 아닌지, 고객 응답인지 사내 로그인지 등은 서비스에서 정한다.
        - core은 단지 "마스킹을 하라"라는 시그널을 받을 뿐이다.
        """
        if should_mask and 500 <= self.status_code <= 599:
            return ErrorSpec(
                code="internal_error",
                message="Internal server error",
                status_code=self.status_code,
                target=self.target,
                meta=None,
                trace_id=self.trace_id,
                exc_type=self.exc_type,
                stack=None,
                severity=self.severity,
            )

        return self



def _safe_stack(exc: Exception, *, include_stack: bool) -> Optional[str]:
    """
    예외에서 stack trace 문자열을 안전하게 추출.
    prod에선 기본적으로 None을 돌려주도록 설계.
    서비스 레이어에서 원하면 override된 stack을 넣어도 되고, 안 넣어도 된다.
    """
    if not include_stack:
        return None
    return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def _is_app_error(exc: Exception) -> bool:
    """
    비즈니스 레이어에서 raise하는 의도적 예외(AppError 계열)인지 duck-typing으로 판정한다.
    상속 강제 안 하고, 필드 형태만 맞으면 AppError 취급한다.

    우리가 기대하는 최소 인터페이스:
    - .code: str
    - .message: str
    - .status_code: int
    - (optional) .target: str | None
    - (optional) .meta: dict | None
    - (optional) .severity or .level 같은 게 있다면 나중에 반영 가능
    """
    has_code = hasattr(exc, "code") and isinstance(getattr(exc, "code"), str)
    has_msg = hasattr(exc, "message") and isinstance(getattr(exc, "message"), str)
    has_status = hasattr(exc, "status_code") and isinstance(getattr(exc, "status_code"), int)
    return has_code and has_msg and has_status


def from_exception_minimal(
    exc: Exception,
    *,
    trace_id: str,
    include_stack: bool,
) -> ErrorSpec:
    """
    core가 제공하는 '최소한의' 정규화.
    이 함수는 core가 책임질 수 있는 가장 좁은 영역만 다룬다.

    - AppError 형태(비즈니스 에러)면 그대로 스펙화.
      -> 주로 사용자의 잘못된 요청 / 도메인 규칙 위반 / 권한 부족 등.
      -> 일반적으로 retry 불필요한 유형.
      -> severity는 기본 WARNING 정도로 본다.

    - 나머지는 전부 내부 서버 오류(알 수 없는 예외)로 본다.
      -> status_code=500 / code="internal_error"
      -> severity="ERROR"
      -> stack은 prod가 아니면 담아준다.

    중요한 점:
    - 여기서는 FastAPI의 RequestValidationError, StarletteHTTPException, SQLAlchemy IntegrityError
      이런 구체 프레임워크/인프라 예외는 다루지 않는다.
    - 그건 API나 Worker 등 '서비스 레이어 핸들러'에서 각자 해석한 뒤
      ErrorSpec(...)을 직접 만들어야 한다.
    """

    if _is_app_error(exc):
        return ErrorSpec(
            code=getattr(exc, "code"),
            message=getattr(exc, "message"),
            status_code=getattr(exc, "status_code"),
            target=getattr(exc, "target", None),
            meta=getattr(exc, "meta", None),
            trace_id=trace_id,
            exc_type=exc.__class__.__name__,
            stack=None,  # 비즈니스 에러는 굳이 스택 노출까지 필요 없음(보통 우리가 의도적으로 raise 했으니까)
            severity="WARNING",
        )

    # 알 수 없는 / 인프라 / 런타임 예외 → 내부 서버 에러 취급
    return ErrorSpec(
        code="internal_error",
        message="Internal server error",
        status_code=500,
        target=None,
        meta={"type": exc.__class__.__name__},
        trace_id=trace_id,
        exc_type=exc.__class__.__name__,
        stack=_safe_stack(exc, include_stack=include_stack),
        severity="ERROR",
    )


def build_log_fields(
    spec: ErrorSpec,
    *,
    ctx: Optional[Dict[str, Any]] = None,
    redact_keys: Optional[set[str]] = None,
) -> Dict[str, Any]:
    """
    공통 로그 필드 빌더.
    서비스 레이어(API / Worker / etc)가 logger.log(...) 호출할 때 extra로 붙일 dict를 만들어준다.

    ctx:
      서비스가 남기고 싶은 컨텍스트 (ex: {"path": "/users", "method": "POST"})
      여기서 받은 값은 "ctx.{key}" 형태로 들어간다.

    redact_keys:
      meta 안에서 민감정보 키를 빼고 싶으면 서비스 쪽에서 넘긴다.
      예: prod 환경이면 {"db_msg", "params"} 이런 식으로 넘겨서 로그 마스킹.
      core는 어떤 키가 민감한지 모른다. (이것도 서비스 책임)
    """
    out: Dict[str, Any] = {
        "trace_id": spec.trace_id,
        "code": spec.code,
        "status": spec.status_code,
        "severity": spec.severity,
        "exc_type": spec.exc_type,
    }

    if spec.meta is not None:
        safe_meta = dict(spec.meta)
        if redact_keys:
            for k in redact_keys:
                if k in safe_meta:
                    safe_meta.pop(k, None)
        out["meta"] = safe_meta

    if ctx:
        for k, v in ctx.items():
            out[f"ctx.{k}"] = v

    return out
