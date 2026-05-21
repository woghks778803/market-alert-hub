from typing import Callable, Any
import logging
from datetime import datetime

# from tenacity import retry, stop_after_attempt, wait_exponential
from app.core import dto as CoreDTO
from app.core.constants import OutboxStatus, OutboxEventType, ChannelCode
from app.core.util.trace import get_trace_id
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import InternalServerError, ValidationAppError
from app.domain import OutboxDTO, OutboxRule, OutboxPort, CryptoPort

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        hmac: CryptoPort.TokenHasher,
        outbox_event: OutboxPort.OutboxEvent
    ) -> None:
        self._uow_factory = uow_factory
        self._hmac = hmac
        self._outbox_event = outbox_event

    def create_outbox(
        self,
        trace_id: str,
        outbox_fingerprint_dict: dict | None,
        event_type: str,
        aggregate_type: str,
        aggregate_id: int,
        payload: dict[str, Any],
    ) -> None:
        with self._uow_factory() as uow:
            outbox_fingerprint = to_canonical_json(outbox_fingerprint_dict)
            if outbox_fingerprint:
                outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)
            else:
                outbox_fingerprint = None

            uow.outboxs.add_outbox(
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

    def _decide_retry(
        self,
        result: CoreDTO.HandlerResult,
        outbox_attempt: OutboxDTO.OutboxAttemptCreate,
        outbox_update: OutboxDTO.OutboxUpdate,
        event_type,
    ):
        with self._uow_factory() as uow:

            if result.retryable:
                if OutboxEventType.AUTH_EMAIL_VERIFY == event_type:
                    provider = uow.channels.get_provider_by_code(ChannelCode.EMAIL.value)

                    if not provider:
                        raise NotFoundError(
                            "Not found channel provider", target="channel_provider"
                        )

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
                if result.success:
                    outbox_update.status = OutboxStatus.SENT
                    outbox_attempt.result_message = "Done"
                else:
                    outbox_update.status = OutboxStatus.FAILED

            return outbox_attempt, outbox_update

    # @retry(
    #     stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    # )
    def deliver_outbox(self, outbox_id: int, dispatch_fn) -> None:
        event_type = None
        should_record = False # 조회, 검증 후 저장 여부

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

                should_record = True
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
            if should_record:
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
