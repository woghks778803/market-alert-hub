from typing import Callable
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from app.domain.uow import UnitOfWork
from app.core.constants import OutboxStatus
from app.core.datetime_utils import utcnow
from app.domain import OutboxDTO, OutboxRule

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def enqueue_outbox_pending(self, limit: int, q_outbox):
        with self._uow_factory() as uow:
            outbox_filter = OutboxDTO.OutboxFilter(status=OutboxStatus.PENDING)
            ids = uow.outboxs.list_outboxs_by_filter(outbox_filter, limit=limit)  # SELECT ... FOR UPDATE
            if not ids:
                return 0
            
            outbox_filter = OutboxDTO.OutboxFilter(ids=ids)
            outbox_update = OutboxDTO.OutboxUpdate(status=OutboxStatus.SENDING)

            uow.outboxs.update_outbox_by_filter(filters=outbox_filter, updates=outbox_update)

            # 각 이벤트를 RQ 큐에 등록
            for oid in ids:
                q_outbox.enqueue(
                    "app.jobs.process_outbox.deliver_outbox_event",
                    oid,
                    job_id=f"outbox-{oid}",  # 중복 enqueue 방지
                    retry=None
                )
                logger.info("enqueued outbox id=%s", oid)

            uow.commit()  # ✅ enqueue까지 성공하면 commit
            return len(ids)

    # @retry(
    #     stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    # )
    def deliver_outbox(self, outbox_id: int, dispatch_fn) -> None:

        with self._uow_factory() as uow:
            row = uow.outboxs.get_by_outbox_id(outbox_id)
            if row is None:
                logger.warning("outboxs not found id=%s", outbox_id)
                return
            if row.status != OutboxStatus.SENDING:
                logger.info("skip id=%s status=%s", outbox_id, row.status)
                return
        
        outbox_filter = OutboxDTO.OutboxFilter(id=row.id)
        payload = OutboxRule.parse_payload(getattr(row, "payload", None))
        attempts = row.attempts + 1
        try:
            dispatch_fn(
                event_type=row.event_type, payload=payload
            )

            with self._uow_factory() as uow:
                
                outbox_update = OutboxDTO.OutboxUpdate(attempts=attempts, status=OutboxStatus.SENT)
                uow.outboxs.update_outbox_by_filter(filters=outbox_filter, updates=outbox_update)
                uow.commit()
        except Exception as e:
            with self._uow_factory() as uow:
                
                if attempts < OutboxRule.MAX_ATTEMPTS:
                    next_at = utcnow() + OutboxRule.compute_backoff(
                        attempts
                    )
                    outbox_update = OutboxDTO.OutboxUpdate(attempts=attempts, status=OutboxStatus.PENDING, next_run_at=next_at)
                    uow.outboxs.update_outbox_by_filter(filters=outbox_filter, updates=outbox_update)
                else:
                    outbox_update = OutboxDTO.OutboxUpdate(attempts=attempts, status=OutboxStatus.FAILED)
                    uow.outboxs.update_outbox_by_filter(filters=outbox_filter, updates=outbox_update)

                logger.exception("process failed outbox id=%s attempts=%s", row.id, attempts)
                uow.commit()
