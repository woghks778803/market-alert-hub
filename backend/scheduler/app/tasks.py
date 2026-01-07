import uuid
import logging
from app.core.constants import OutboxEventType

logger = logging.getLogger(__name__)

class IntervalTask:
    """
    interval_sec 단위로 slot이 바뀔 때마다 handler를 1번 호출한다.
    (예: interval_sec=60이면 매 분 slot=epoch//60)
    """

    def __init__(self, name, interval_sec, handler):
        self.name = name
        self.interval_sec = int(interval_sec)
        self.handler = handler
        self._last_slot = None

    def tick(self, now_epoch, ctx):
        slot = now_epoch // self.interval_sec
        if self._last_slot == slot:
            return
        self._last_slot = slot
        self.handler(ctx, slot, now_epoch)


def build_default_tasks(config):
    """
    환경변수 기반 기본 태스크 구성
    """

    return [
        IntervalTask(
            OutboxEventType.SYNC_EXCHANGES,
            config.sync_interval_sec,
            _handle_sync_exchanges,
        ),
        IntervalTask(
            OutboxEventType.SYNC_SYMBOLS,
            config.sync_interval_sec,
            _handle_sync_symbols,
        ),
        # IntervalTask(
        #     OutboxEventType.TRIGGER_ALERTS,
        #     config.trig_interval_sec,
        #     _handle_trigger_alerts,
        # ),
        IntervalTask(
            OutboxEventType.PERSIST_SNAPSHOTS,
            config.snapshot_interval_sec,
            _handle_persist_snapshots,
        ),
    ]

def _handle_sync_exchanges(ctx, slot, now_epoch):
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

def _handle_sync_symbols(ctx, slot, now_epoch):
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
    _insert_outbox(
        ctx, OutboxEventType.SYNC_SYMBOLS, outbox_fingerprint_dict, payload
    )


def _handle_trigger_alerts(ctx, slot, now_epoch):
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


def _handle_persist_snapshots(ctx, slot, now_epoch):
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
