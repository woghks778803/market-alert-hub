from typing import Callable
from datetime import datetime, timedelta, timezone
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.domain.uow import UnitOfWork
from app.core.constants import OutboxStatus
from app.domain import OutboxDTO, OutboxRule

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def fetch_and_mark_sending(self, limit: int) -> list[int]:
        with self._uow_factory() as uow:
            ids = uow.outboxs.due_pending_ids(limit)
            if ids:
                uow.outboxs.mark_inflight(ids)
            # __exit__에서 커밋
            return ids

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    def process_one(self, event_id: int, dispatch_fn) -> None:
        with self._uow_factory() as uow:
            row = uow.outboxs.get(event_id)
            if row is None:
                logger.warning("outboxs not found id=%s", event_id)
                return
            if row.status != OutboxStatus.SENDING:
                logger.info("skip id=%s status=%s", event_id, row.status)
                return

            payload = OutboxRule.parse_payload(getattr(row, "payload_json", None))
            try:
                dispatch_fn(
                    event_type=row.event_type, channel=row.channel, payload=payload
                )
                uow.outboxs.mark_sent(row.id, row.attempts)
                # __exit__ commit
            except Exception as e:
                attempts = row.attempts + 1
                if attempts < OutboxRule.MAX_ATTEMPTS:
                    next_at = datetime.now(timezone.utc) + OutboxRule.compute_backoff(
                        attempts
                    )
                    uow.outboxs.mark_pending(row.id, attempts, next_at, str(e))
                else:
                    uow.outboxs.mark_failed(row.id, attempts, str(e))
                logger.exception("process failed id=%s attempts=%s", row.id, attempts)
                raise
