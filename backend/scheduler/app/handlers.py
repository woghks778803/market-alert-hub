import logging
from app.core.constants import OutboxEventType, SYSTEM
from app.core.util.trace import get_trace_id

logger = logging.getLogger(__name__)


def handle_fetch_rss(ctx, slot, now_epoch, interval_sec):
    rss_sources = ctx.svcs.newses.list_rss_source_by_filter()

    for rss_source in rss_sources:
        outbox_fingerprint_dict = {
            "event_type": OutboxEventType.FETCH_RSS_SOURCES.value,
            "aggregate_type": "rss_source",
            "aggregate_id": rss_source.id,
            "slot": slot,
        }
        payload = {
            "slot": slot,
            "requested_at_epoch": now_epoch,
            "interval_sec": interval_sec,
            "rss": {
                "id": rss_source.id,
                "code": rss_source.code,
            },
        }
        _insert_outbox(
            ctx, OutboxEventType.FETCH_RSS_SOURCES, outbox_fingerprint_dict, payload
        )

def handle_cleanup_deleted_users(ctx, slot, now_epoch, interval_sec):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.CLEANUP_DELETED_USERS.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }

    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }

    _insert_outbox(
        ctx,
        OutboxEventType.CLEANUP_DELETED_USERS,
        outbox_fingerprint_dict,
        payload,
    )


def handle_sync_exchanges(ctx, slot, now_epoch, interval_sec):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.SYNC_EXCHANGES.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }

    _insert_outbox(
        ctx, OutboxEventType.SYNC_EXCHANGES, outbox_fingerprint_dict, payload
    )


def handle_sync_symbols(ctx, slot, now_epoch, interval_sec):
    exchanges = ctx.svcs.markets.list_exchange_by_filter()

    for ex in exchanges:
        outbox_fingerprint_dict = {
            "event_type": OutboxEventType.SYNC_SYMBOLS.value,
            "aggregate_type": "exchange",
            "aggregate_id": ex.id,
            "slot": slot,
        }
        payload = {
            "slot": slot,
            "requested_at_epoch": now_epoch,
            "interval_sec": interval_sec,
            "exchange": {
                "id": ex.id,
                "code": ex.code,
            },
        }
        _insert_outbox(
            ctx, OutboxEventType.SYNC_SYMBOLS, outbox_fingerprint_dict, payload
        )


def handle_sync_tickers(ctx, slot, now_epoch, interval_sec):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.SYNC_TICKERS.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }

    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }

    _insert_outbox(
        ctx,
        OutboxEventType.SYNC_TICKERS,
        outbox_fingerprint_dict,
        payload,
    )


def handle_sync_alerts(ctx, slot, now_epoch, interval_sec):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.SYNC_ALERTS.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }

    _insert_outbox(
        ctx, OutboxEventType.SYNC_ALERTS, outbox_fingerprint_dict, payload
    )


def handle_dispatch_alert_events(ctx, slot, now_epoch, interval_sec):
    # shard_total=0
    # shard_index=0

    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.DISPATCH_ALERT_EVENTS.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }
    _insert_outbox(
        ctx, OutboxEventType.DISPATCH_ALERT_EVENTS, outbox_fingerprint_dict, payload
    )


def handle_persist_snapshots(ctx, slot, now_epoch, interval_sec):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.PERSIST_SNAPSHOTS.value,
        "aggregate_type": SYSTEM,
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
        "interval_sec": interval_sec,
    }
    _insert_outbox(
        ctx, OutboxEventType.PERSIST_SNAPSHOTS, outbox_fingerprint_dict, payload
    )


def _insert_outbox(ctx, event_type, outbox_fingerprint_dict, payload):
    trace_id = get_trace_id()
    logger.info(f"scheduler.insert_outbox trace_id={trace_id}, event_type={event_type}")

    ctx.svcs.outboxs.create_outbox(
        trace_id=trace_id,
        outbox_fingerprint_dict=outbox_fingerprint_dict,
        event_type=event_type,
        aggregate_type=outbox_fingerprint_dict["aggregate_type"],
        aggregate_id=outbox_fingerprint_dict["aggregate_id"],
        payload=payload,
    )
