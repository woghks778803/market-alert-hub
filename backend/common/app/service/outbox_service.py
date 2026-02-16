from typing import Callable, Any
import logging
from datetime import datetime

# from tenacity import retry, stop_after_attempt, wait_exponential
from app.core import dto as CoreDTO
from app.core.constants import OutboxStatus, OutboxEventType
from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import InternalServerError, ValidationAppError
from app.domain import OutboxDTO, OutboxRule, CryptoPort

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        hmac: CryptoPort.TokenHasher,
    ) -> None:
        self._uow_factory = uow_factory
        self._hmac = hmac

    def create_outbox(
        self,
        trace_id: str,
        outbox_fingerprint_dict: dict | None,
        event_type: str,
        aggregate_type: str,
        aggregate_id: int,
        payload: dict[str, Any],
    ) -> OutboxDTO.Outbox:
        with self._uow_factory() as uow:
            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint:
                outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)
            else:
                outbox_fingerprint = None

            row = uow.outboxs.add_outbox(
                OutboxDTO.OutboxCreate(
                    trace_id=trace_id,
                    event_type=event_type,
                    aggregate_type=aggregate_type,
                    aggregate_id=aggregate_id,
                    outbox_fingerprint=outbox_fingerprint,
                    payload=payload,
                    status=OutboxStatus.PENDING,
                    attempts=0,
                ),
                False,
            )

            uow.commit_outbox_idempotent()
            return row

    def enqueue_outbox_pending(self, limit: int, q_outbox):
        with self._uow_factory() as uow:
            outbox_filter = OutboxDTO.OutboxFilter(
                status=OutboxStatus.PENDING, next_run_at=utcnow()
            )
            ids = uow.outboxs.list_outboxs_by_filter(outbox_filter, limit=limit)
            if not ids:
                return 0

            outbox_filter = OutboxDTO.OutboxFilter(ids=ids)
            outbox_update = OutboxDTO.OutboxUpdate(status=OutboxStatus.SENDING)

            uow.outboxs.update_outbox_by_filter(
                filters=outbox_filter, updates=outbox_update
            )

            # 각 이벤트를 RQ 큐에 등록
            for oid in ids:
                q_outbox.enqueue(
                    "app.tasks.deliver_outbox_event",
                    oid,
                    job_id=f"outbox-{oid}",  # 중복 outbox enqueue 방지
                    retry=None,
                )
                logger.info("enqueued outbox id=%s", oid)

            uow.commit()  #  enqueue까지 성공하면 commit
            return len(ids)

    def _decide_retry(
        self,
        result: CoreDTO.HandlerResult,
        outbox_attempt: OutboxDTO.OutboxAttemptCreate,
        outbox_update: OutboxDTO.OutboxUpdate,
        event_type,
    ):
        with self._uow_factory() as uow:

            if result.retryable:
                if OutboxEventType.EMAIL_AUTH_CODE == event_type:
                    provider = uow.channels.get_channel_by_code("EMAIL")
                    policy = provider.retry_policy  # JSON → dict 파싱
                    if not policy:
                        raise InternalServerError(
                            "retry policy not configured",
                            target="channel_provider.retry_policy",
                        )
                    if outbox_update.attempts is None:
                        raise ValidationAppError(
                            "attempts not found",
                            target="attempts",
                        )

                    max_attempts = policy["max_attempts"]
                    base_delay = policy["base_delay_sec"]
                    max_delay = policy["max_delay_sec"]

                    if outbox_update.attempts < max_attempts:
                        outbox_attempt.retryable = True
                        outbox_update.status = OutboxStatus.PENDING
                        delay = OutboxRule.compute_backoff(
                            outbox_update.attempts,
                            base_delay_sec=base_delay,
                            max_delay_sec=max_delay,
                        )
                        outbox_update.next_run_at = utcnow() + delay

                        logger.info(
                            f"max_attempts={max_attempts}, base_delay={base_delay}, max_delay={max_delay}, attempts={outbox_update.attempts},  next_at={outbox_update.next_run_at}"
                        )

                    else:
                        outbox_attempt.retryable = False
                        outbox_update.status = OutboxStatus.FAILED
            else:
                outbox_attempt.success = result.success
                outbox_attempt.retryable = result.retryable
                outbox_attempt.result_message = "Done"
                if result.success:
                    outbox_update.status = OutboxStatus.SENT
                else:
                    outbox_update.status = OutboxStatus.FAILED

            return outbox_attempt, outbox_update

    # @retry(
    #     stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    # )
    def deliver_outbox(self, outbox_id: int, dispatch_fn) -> None:
        event_type = None

        outbox_attempt = OutboxDTO.OutboxAttemptCreate(
            outbox_id=outbox_id,
            attempt_no=0,
            success=0,
            retryable=0,
            result_code=None,
            result_message=None,
            result_payload={},
            started_at=utcnow(),
            finished_at=None,
        )
        outbox_update = OutboxDTO.OutboxUpdate(
            attempts=0,
            status=OutboxStatus.SENDING,
            next_run_at=utcnow(),
        )

        try:
            with self._uow_factory() as uow:
                row = uow.outboxs.get_by_outbox_id(outbox_id)
                if not row:
                    logger.warning("outboxs not found id=%s", outbox_id)
                    return
                if row.status != OutboxStatus.SENDING:
                    logger.info("skip id=%s status=%s", outbox_id, row.status)
                    return

                payload = OutboxRule.parse_payload(getattr(row, "payload", None))
                outbox_attempt.attempt_no = outbox_update.attempts = row.attempts + 1
                outbox_filter = OutboxDTO.OutboxFilter(id=row.id)
                event_type = row.event_type

            result: CoreDTO.HandlerResult = dispatch_fn(
                event_type=event_type, payload=payload
            )

            outbox_attempt.result_code = result.result_code
            outbox_attempt.result_message = result.result_message
            outbox_attempt.result_payload = result.result_payload

            outbox_attempt, outbox_update = self._decide_retry(
                result, outbox_attempt, outbox_update, event_type
            )

        except Exception as e:
            outbox_attempt.retryable = False
            outbox_update.status = OutboxStatus.FAILED
            response = getattr(e, "response", None)
            error = response.get("Error", {}) if isinstance(response, dict) else {}
            outbox_attempt.result_code = error.get("Code") or e.__class__.__name__
            outbox_attempt.result_message = error.get("Message") or str(e)
            outbox_attempt.result_payload = {
                "error_code": outbox_attempt.result_code,
                "error_message": outbox_attempt.result_message,
            }

            logger.exception(
                "process failed outbox id=%s attempts=%s",
                outbox_id,
                outbox_update.attempts,
            )
        finally:
            with self._uow_factory() as uow:
                outbox_attempt.finished_at = utcnow()
                uow.outboxs.add_outbox_attempt(
                    outbox_attempt,
                    False,
                )
                uow.outboxs.update_outbox_by_filter(
                    filters=outbox_filter,
                    updates=outbox_update,
                )

                uow.commit()
