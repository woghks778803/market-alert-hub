from uuid import uuid4
from app.core.constants import OutboxEventType
from app.core.util.trace import set_trace_id, clear_trace_id
from app.handlers import (
    handle_cleanup_deleted_users,
    handle_persist_snapshots,
    handle_sync_exchanges,
    handle_sync_symbols,
    handle_sync_tickers,
    handle_sync_alerts,
    handle_dispatch_alert_events,
    handle_fetch_news_feeds,
)


class IntervalTask:
    """
    interval_sec 단위로 slot이 바뀔 때마다 handler를 1번 호출한다.
    (예: interval_sec=60이면 매 분 slot=epoch//60)
    """

    def __init__(self, name, interval_sec, handler):
        interval_sec = int(interval_sec)
        if interval_sec <= 0:
            raise ValueError("interval_sec must be positive")

        self.name = name
        self.interval_sec = interval_sec
        self.handler = handler
        self._last_slot = None

    def tick(self, now_epoch, ctx):
        slot = now_epoch // self.interval_sec
        if self._last_slot == slot:
            return
        self._last_slot = slot
        set_trace_id(str(uuid4()))
        try:
            self.handler(ctx, slot, now_epoch, self.interval_sec)
        finally:
            clear_trace_id()


def build_default_tasks(config):
    """
    환경변수 기반 기본 태스크 구성
    """

    return [
        IntervalTask(
            OutboxEventType.FETCH_NEWS_FEED,
            config.rss_interval_sec,
            handle_fetch_news_feeds,
        ),
        IntervalTask(
            OutboxEventType.CLEANUP_DELETED_USERS,
            config.cleanup_interval_sec,
            handle_cleanup_deleted_users,
        ),
        IntervalTask(
            OutboxEventType.SYNC_EXCHANGES,
            config.exchanges_interval_sec,
            handle_sync_exchanges,
        ),
        IntervalTask(
            OutboxEventType.SYNC_SYMBOLS,
            config.symbols_interval_sec,
            handle_sync_symbols,
        ),
        IntervalTask(
            OutboxEventType.SYNC_TICKERS,
            config.tickers_interval_sec,
            handle_sync_tickers,
        ),
        IntervalTask(
            OutboxEventType.SYNC_ALERTS,
            config.alerts_interval_sec,
            handle_sync_alerts,
        ),
        IntervalTask(
            OutboxEventType.DISPATCH_ALERT_EVENTS,
            config.alert_events_interval_sec,
            handle_dispatch_alert_events,
        ),
        *[
            IntervalTask(
                OutboxEventType.PERSIST_SNAPSHOTS,
                interval_sec,
                handle_persist_snapshots,
            )
            for interval_sec in config.snapshot_intervals_sec
        ],
    ]
