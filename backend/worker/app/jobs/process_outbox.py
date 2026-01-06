import logging
import uuid
from typing import Any, Callable, Mapping, Protocol, runtime_checkable

from app.core.constants import EmailVerificationStatus, OutboxEventType
from app.core.util.datetime import utcnow, ensure_utc
from app.domain.shared.errors import ValidationAppError

# from app.service.factory import ServiceFactory
from app.runtime.app_context import WorkerContext
from app.wiring import get_app_context


@runtime_checkable
class RedisClientLike(Protocol):
    """
    worker jobs 레벨에서 필요한 최소 API.
    - redis-py(외부 라이브러리) 타입을 여기로 끌고 오지 않기 위한 목적.
    """

    def set(
        self,
        key: str,
        value: bytes,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool: ...

    def ttl(self, key: str) -> int: ...
    def delete(self, key: str) -> int: ...
    def conn(self) -> Any: ...


logger = logging.getLogger(__name__)
Handler = Callable[[WorkerContext, Mapping[str, Any]], Any]


# ---- helpers --------------------------------------------------------------


def _require(payload: Mapping[str, Any], key: str, *, target: str) -> Any:
    v = payload.get(key)
    if v is None or v == "":
        raise ValidationAppError(f"payload '{key}' is required", target=target)
    return v


def _try_acquire_lock(
    redis_client: RedisClientLike, key: str, ttl_sec: int
) -> str | None:
    token = uuid.uuid4().hex
    redis_conn = redis_client.conn()
    ok = redis_conn.set(key, token.encode("utf-8"), nx=True, ex=ttl_sec)
    return token if ok else None


def _release_lock(redis_client: RedisClientLike, key: str, token: str) -> None:
    # 토큰 일치할 때만 해제(최소 안전장치)
    redis_conn = redis_client.conn()
    cur = redis_conn.get(key)
    if cur is None:
        return
    try:
        cur_s = cur.decode("utf-8", errors="ignore")
    except Exception:
        return
    if cur_s == token:
        redis_client.delete(key)


def _skip(reason: str) -> dict:
    return {"ok": True, "skipped": True, "reason": reason}


# ---- handlers -------------------------------------------------------------


def _handle_email_auth_code(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> Any:
    user_id = _require(payload, "user_id", target="payload.user_id")
    email_verification_id = _require(
        payload, "email_verification_id", target="payload.email_verification_id"
    )
    verify_token = _require(payload, "verify_token", target="payload.verify_token")

    user_email_info = ctx.svcs.users.get_user_email_info(user_id=user_id)

    # ---  발송 직전 재검사(중요) ---
    email_verification = ctx.svcs.users.get_email_verification_by_id(
        email_verification_id=email_verification_id
    )

    now = utcnow()
    if email_verification.status != EmailVerificationStatus.PENDING:
        return _skip(f"status={email_verification.status}")

    expires_at = ensure_utc(email_verification.expires_at)
    if expires_at <= now:
        return _skip("expired")

    lock_key = f"lock:email_verify_send:{email_verification_id}"
    token = _try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        return _skip("locked")

    try:
        ses_result = ctx.svcs.emails.send_verify(
            user=user_email_info,
            verify_token=verify_token,
        )
        ctx.svcs.users.set_email_verification_sent(
            email_verification_id=email_verification_id
        )
        return ses_result
    finally:
        _release_lock(ctx.redis_client, lock_key, token)


_HANDLERS: dict[OutboxEventType, Handler] = {
    OutboxEventType.EMAIL_AUTH_CODE: _handle_email_auth_code,
}


def _dispatch(
    ctx: WorkerContext,
    *,
    event_type: str,
    payload: Mapping[str, Any],
) -> Any:
    logger.info("dispatch event_type=%s keys=%s", event_type, list(payload.keys()))

    handler = _HANDLERS.get(OutboxEventType(event_type))
    if handler is None:
        raise ValidationAppError(
            f"unsupported event_type={event_type}", target="event_type"
        )

    return handler(ctx, payload)


# ---- job entrypoint -------------------------------------------------------


def deliver_outbox_event(outbox_id: int) -> None:
    """
    RQ가 실행하는 잡 엔트리.
    OutboxService가 트랜잭션/상태 전이를 담당하고,
    실제 발송은 handler로 위임한다.
    """
    ctx = get_app_context()

    ctx.svcs.outboxs.deliver_outbox(
        outbox_id=outbox_id,
        dispatch_fn=lambda event_type, payload: _dispatch(
            ctx,
            event_type=event_type,
            payload=payload,
        ),
    )
