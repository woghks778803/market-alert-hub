from typing import Any, Mapping
from app.core.constants import OutboxEventType, LOCK
from app.core.util.datetime import utcnow, ensure_utc
from app.runtime.app_context import WorkerContext
from app.util.utils import require, try_acquire_lock, release_lock
from app.exception_handlers import SkipHandler, RetryHandler, FatalHandler


def handle_auth_password_reset(
    ctx: WorkerContext,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    redis_key_prefix = f"{{{ctx.config.key_prefix}}}"

    user_id = require(payload, "user_id", target="payload.user_id")
    password_reset_id = require(
        payload, "password_reset_id", target="payload.password_reset_id"
    )
    verify_token = require(payload, "verify_token", target="payload.verify_token")

    user_email_info = ctx.svcs.users.get_user_email_info(user_id=user_id)

    password_reset = ctx.svcs.users.get_password_reset_by_id(
        password_reset_id=password_reset_id
    )

    now = utcnow()

    expires_at = ensure_utc(password_reset.expires_at)
    if expires_at <= now:
        raise SkipHandler("expired")

    lock_key = f"{redis_key_prefix}:{LOCK}:{OutboxEventType.AUTH_PASSWORD_RESET.value}:{password_reset_id}"
    token = try_acquire_lock(
        ctx.redis_client, lock_key, ttl_sec=ctx.config.outbox_send_lock_ttl_sec
    )
    if not token:
        raise SkipHandler("locked")

    try:
        ses_result = ctx.svcs.emails.send_password_reset(
            user=user_email_info,
            verify_token=verify_token,
        )
        ctx.svcs.users.change_password_reset_sent(password_reset_id=password_reset_id)
        return ses_result

    except (TimeoutError, ConnectionError) as e:
        raise RetryHandler(
            "email_send_retry",
            meta={"provider": "EMAIL", "error": str(e)},
        ) from e

    except Exception as e:
        raise FatalHandler(
            "email_send_fatal",
            meta={"provider": "EMAIL", "error": str(e)},
        ) from e
    finally:
        release_lock(ctx.redis_client, lock_key, token)
