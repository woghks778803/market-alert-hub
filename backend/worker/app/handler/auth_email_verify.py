from typing import Any, Mapping
from app.core.constants import OutboxEventType, EmailVerificationStatus, LOCK
from app.core.util.datetime import utcnow, ensure_utc
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, RetryHandler, FatalHandler


def handle_auth_email_verify(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    app_name = ctx.config.app_name
    deploy_env = ctx.config.deploy_env

    user_id = require(payload, "user_id", target="payload.user_id")
    email_verification_id = require(
        payload, "email_verification_id", target="payload.email_verification_id"
    )
    verify_token = require(payload, "verify_token", target="payload.verify_token")

    user_email_info = ctx.svcs.users.get_user_email_info(user_id=user_id)

    # ---  발송 직전 재검사(중요) ---
    email_verification = ctx.svcs.users.get_email_verification_by_id(
        email_verification_id=email_verification_id
    )

    now = utcnow()
    if email_verification.status != EmailVerificationStatus.PENDING:
        raise SkipHandler(f"status={email_verification.status}")

    expires_at = ensure_utc(email_verification.expires_at)
    if expires_at <= now:
        raise SkipHandler("expired")

    lock_key = (
        f"{app_name}:{deploy_env}:{LOCK}:{OutboxEventType.AUTH_EMAIL_VERIFY.value}:{email_verification_id}"
    )
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        ses_result = ctx.svcs.emails.send_email_verify(
            user=user_email_info,
            verify_token=verify_token,
        )
        ctx.svcs.users.change_email_verification_sent(
            email_verification_id=email_verification_id
        )
        return ses_result

    except (TimeoutError, ConnectionError) as e:
        raise RetryHandler(
            "email_send_failed",
            meta={"provider": "EMAIL", "error": str(e)},
        ) from e

    except Exception as e:
        raise FatalHandler(
            "email_send_fatal",
            meta={"provider": "EMAIL", "error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
