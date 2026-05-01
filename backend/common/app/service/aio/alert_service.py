import logging
import json
from decimal import Decimal
from typing import Callable, Sequence, Any
from collections.abc import Mapping
from datetime import datetime

from app.core.constants import AlertStatus
from app.core.util.datetime import utcnow
from app.core.util.serialization import json_safe, decode_bytes, decode_bytes_dict
from app.domain import AlertDTO, AlertRule, AlertPort
from app.domain.shared.async_uow import AsyncUnitOfWork

logger = logging.getLogger(__name__)

class AlertService:
    def __init__(
        self, 
        uow_factory: Callable[[], AsyncUnitOfWork],
        alert_event: AlertPort.AsyncAlertEvent,
        alert_snapshot: AlertPort.AsyncAlertSnapshot,
        alert_bucket: AlertPort.AsyncAlertBucket,
    ) -> None:
        self._uow_factory = uow_factory
        self._alert_event = alert_event
        self._alert_snapshot = alert_snapshot
        self._alert_bucket = alert_bucket

    async def persist_alert_events(
        self,
        *,
        consumer_name: str,
        batch_size: int,
        block_ms: int,
    ) -> int:
        messages = await self._alert_event.read_persist_alert_events(
            consumer_name=consumer_name,
            count=batch_size,
            block_ms=block_ms,
        )

        if not messages:
            return 0

        message_ids: list[str] = []
        rows: list[AlertDTO.AlertEventCreate] = []
        once_alert_ids: set[int] = set()
        once_remove_items: dict[int, str] = {}

        for message_id, fields in messages:
            raw_payload = fields.get("p")

            if raw_payload is None:
                logger.warning(
                    "alert_event_stream_missing_payload message_id=%s",
                    message_id,
                )
                message_ids.append(message_id)
                continue

            raw_payload = decode_bytes(raw_payload)
            payload = json.loads(raw_payload)

            # alert is_once 기능 처리
            if payload.get("is_once") is True:
                alert_id = payload["alert_id"]
                bucket_key = payload.get("bucket_key")

                once_alert_ids.add(alert_id)
                if bucket_key:
                    once_remove_items[alert_id] = bucket_key
        
            rows.append(self._to_alert_event_create(payload))
            message_ids.append(message_id)

        if not rows:
            if message_ids:
                await self._alert_event.ack_persist_alert_events(
                    message_ids=message_ids,
                )

            return 0

        async with self._uow_factory() as uow:
            await uow.alerts.upsert_alert_events(rows)

            if once_alert_ids:
                await uow.alerts.upsert_alerts_status(
                    alert_ids=list(once_alert_ids),
                    status=AlertStatus.PAUSED,
                )

            await uow.commit()
        
        if once_remove_items:
            await self._remove_alert_snapshots(once_remove_items)

        await self._alert_event.ack_persist_alert_events(
            message_ids=message_ids,
        )

        # print("once_alert_ids", once_alert_ids)
        # print("once_remove_items", once_remove_items)
        logger.info(
            "alert_event_persisted count=%s ack_count=%s once_count=%s",
            len(rows),
            len(message_ids),
            len(once_alert_ids),
        )

        return len(rows)

    def _to_alert_event_create(
        self,
        payload: dict[str, Any],
    ) -> AlertDTO.AlertEventCreate:
        trigger_value = payload.get("trigger_value")

        return AlertDTO.AlertEventCreate(
            alert_id=int(payload["alert_id"]),
            exchange_instrument_id=payload.get("exchange_instrument_id"),
            detected_at=payload.get("detected_at"), #  or utcnow()
            trigger_value=(
                Decimal(str(trigger_value))
                if trigger_value is not None
                else None
            ),
            context=payload.get("context"),
            dedup_key=str(payload["dedup_key"]),
        )

    async def _remove_alert_snapshots(
        self,
        items: Mapping[int, str],
    ) -> None:
        if not items:
            return

        alert_ids = set(items.keys())

        bucket_items: dict[str, set[int]] = {}

        for alert_id, bucket_key in items.items():
            bucket_items.setdefault(bucket_key, set()).add(alert_id)

        await self._alert_bucket.remove_alerts_by_bucket(bucket_items)
        await self._alert_snapshot.remove_alerts(alert_ids)