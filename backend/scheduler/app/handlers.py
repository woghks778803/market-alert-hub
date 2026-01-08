import logging
import uuid
from app.core.constants import OutboxEventType

logger = logging.getLogger(__name__)


def handle_sync_exchanges(ctx, slot, now_epoch):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.SYNC_EXCHANGES,
        "aggregate_type": "system",
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
    }

    _insert_outbox(
        ctx, OutboxEventType.SYNC_EXCHANGES, outbox_fingerprint_dict, payload
    )


def handle_sync_symbols(ctx, slot, now_epoch):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.SYNC_SYMBOLS,
        "aggregate_type": "system",
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
    }
    _insert_outbox(ctx, OutboxEventType.SYNC_SYMBOLS, outbox_fingerprint_dict, payload)


def handle_trigger_alerts(ctx, slot, now_epoch):
    # shard_total=0
    # shard_index=0

    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.TRIGGER_ALERTS,
        "aggregate_type": "system",
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
    }
    _insert_outbox(
        ctx, OutboxEventType.TRIGGER_ALERTS, outbox_fingerprint_dict, payload
    )


def handle_persist_snapshots(ctx, slot, now_epoch):
    outbox_fingerprint_dict = {
        "event_type": OutboxEventType.PERSIST_SNAPSHOTS,
        "aggregate_type": "system",
        "aggregate_id": 0,
        "slot": slot,
    }
    payload = {
        "slot": slot,
        "requested_at_epoch": now_epoch,
    }
    _insert_outbox(
        ctx, OutboxEventType.PERSIST_SNAPSHOTS, outbox_fingerprint_dict, payload
    )


def _insert_outbox(ctx, event_type, outbox_fingerprint_dict, payload):
    # ctx는 scheduler 런타임에서 조립된 컨텍스트를 전제 (service_factory/uow/session)
    trace_id = str(uuid.uuid4())
    logger.info(f"scheduler.insert_outbox trace_id={trace_id}, event_type={event_type}")

    ctx.svcs.outboxs.create_outbox(
        trace_id=trace_id,
        outbox_fingerprint_dict=outbox_fingerprint_dict,
        event_type=event_type,
        aggregate_type=outbox_fingerprint_dict["aggregate_type"],
        aggregate_id=outbox_fingerprint_dict["aggregate_id"],
        payload=payload,
    )
