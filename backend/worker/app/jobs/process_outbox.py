import logging
import uuid
from typing import Any, Callable, Mapping

from redis import Redis

from app.wiring import get_app_context, worker_config
from app.service.factory import ServiceFactory
from app.domain import ValidationAppError
from app.core.util.datetime import utcnow, ensure_utc
from app.infra.db.model.email_verification import EmailVerificationStatus

logger = logging.getLogger(__name__)
Handler = Callable[[ServiceFactory, Redis, Mapping[str, Any]], Any]
# ---- helpers --------------------------------------------------------------


def _require(payload: Mapping[str, Any], key: str, *, target: str) -> Any:
    v = payload.get(key)
    if v is None or v == "":
        raise ValidationAppError(f"payload '{key}' is required", target=target)
    return v


def _get_worker_config():
    # worker_config를 "값(bag)"으로 들고 있든, "함수"로 들고 있든 둘 다 대응
    return worker_config() if callable(worker_config) else worker_config


def _try_acquire_lock(r: Redis, key: str, ttl_sec: int) -> str | None:
    token = uuid.uuid4().hex
    ok = r.set(key, token, nx=True, ex=ttl_sec)
    return token if ok else None


def _release_lock(r: Redis, key: str, token: str) -> None:
    # 토큰 일치할 때만 해제(안전)
    cur = r.get(key)
    if cur is None:
        return
    if isinstance(cur, bytes):
        cur = cur.decode("utf-8", errors="ignore")
    if cur == token:
        r.delete(key)


def _skip(reason: str) -> dict:
    return {"ok": True, "skipped": True, "reason": reason}


# ---- handlers -------------------------------------------------------------


def _handle_email_auth_code(
    svcs: ServiceFactory,
    redis_conn: Redis,
    payload: Mapping[str, Any],
) -> Any:
    user_id = _require(payload, "user_id", target="payload.user_id")
    email_verification_id = _require(
        payload, "email_verification_id", target="payload.email_verification_id"
    )
    verify_token = _require(payload, "verify_token", target="payload.verify_token")

    user_email_info = svcs.users.get_user_email_info(user_id=user_id)

    # ---  발송 직전 재검사(중요) ---
    email_verification = svcs.users.get_email_verification_by_id(
        email_verification_id=email_verification_id
    )

    now = utcnow()
    if email_verification.status != EmailVerificationStatus.PENDING:
        return _skip(f"status={email_verification.status}")

    expires_at = ensure_utc(email_verification.expires_at)
    if expires_at <= now:
        return _skip("expired")

    cfg = _get_worker_config()
    lock_key = f"lock:email_verify_send:{email_verification_id}"
    token = _try_acquire_lock(
        redis_conn, lock_key, ttl_sec=cfg.outbox_send_lock_ttl_sec
    )
    if not token:
        return _skip("locked")

    try:
        ses_result = svcs.emails.send_verify(
            user=user_email_info,
            verify_token=verify_token,
        )
        svcs.users.set_email_verification_sent(
            email_verification_id=email_verification_id
        )
        return ses_result
    finally:
        _release_lock(redis_conn, lock_key, token)


_HANDLERS: dict[str, Handler] = {
    "EMAIL_AUTH_CODE": _handle_email_auth_code,
}


def _dispatch(
    svcs: ServiceFactory,
    redis_conn: Redis,
    *,
    event_type: str,
    payload: Mapping[str, Any],
) -> Any:
    logger.info("dispatch event_type=%s keys=%s", event_type, list(payload.keys()))

    handler = _HANDLERS.get(event_type)
    if handler is None:
        raise ValidationAppError(
            f"unsupported event_type={event_type}", target="event_type"
        )

    return handler(svcs, redis_conn, payload)


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
            ctx.svcs,
            ctx.redis_conn,
            event_type=event_type,
            payload=payload,
        ),
    )
