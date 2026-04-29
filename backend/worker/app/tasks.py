import logging
from typing import Any, Callable, Mapping

from app.core.constants import OutboxEventType
from app.runtime.app_context import WorkerContext
from app.core import dto as CoreDTO
from app.wiring import get_app_context
from app.exception_handlers import run_task
from .handler.auth_email_verify import handle_auth_email_verify
from .handler.auth_password_reset import handle_auth_password_reset
from .handler.sync_exchange import handle_sync_exchanges
from .handler.sync_symbol import handle_sync_symbols
from .handler.sync_ticker import handle_sync_tickers
from .handler.sync_alert import handle_sync_alerts
from .handler.dispatch_alert_event import handle_dispatch_alert_events
from .handler.persist_snapshot import handle_persist_snapshots
from .handler.cleanup_deleted_user import handle_cleanup_deleted_users
from .handler.fetch_news_feed import handle_fetch_news_feed
from .handler.translate_news_item import handle_translate_news_items


logger = logging.getLogger(__name__)
Handler = Callable[[WorkerContext, Mapping[str, Any]], Any]

HANDLERS: dict[OutboxEventType, Handler] = {
    OutboxEventType.AUTH_EMAIL_VERIFY: handle_auth_email_verify,
    OutboxEventType.AUTH_PASSWORD_RESET: handle_auth_password_reset,
    OutboxEventType.PERSIST_SNAPSHOTS: handle_persist_snapshots,
    OutboxEventType.SYNC_EXCHANGES: handle_sync_exchanges,
    OutboxEventType.SYNC_SYMBOLS: handle_sync_symbols,
    OutboxEventType.SYNC_TICKERS: handle_sync_tickers,
    OutboxEventType.SYNC_ALERTS: handle_sync_alerts,
    OutboxEventType.DISPATCH_ALERT_EVENTS: handle_dispatch_alert_events,
    OutboxEventType.CLEANUP_DELETED_USERS: handle_cleanup_deleted_users,
    OutboxEventType.FETCH_NEWS_FEED: handle_fetch_news_feed,
    OutboxEventType.TRANSLATE_NEWS_ITEMS: handle_translate_news_items,
}


def _dispatch(
    ctx: WorkerContext,
    *,
    event_type: str,
    payload: Mapping[str, Any],
) -> Any:
    logger.info("dispatch event_type=%s keys=%s", event_type, list(payload.keys()))

    handler = HANDLERS.get(OutboxEventType(event_type))
    if handler is None:
        return CoreDTO.HandlerResult(
            success=False,
            retryable=False,
            result_code="unsupported",
            result_message=f"unsupported event_type={event_type}",
            result_payload={},
        )

    return run_task(deploy_env=ctx.config.deploy_env, fn=lambda: handler(ctx, payload))


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
