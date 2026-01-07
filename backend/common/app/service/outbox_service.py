from typing import Callable, Any
import logging
from datetime import datetime

# from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.constants import OutboxStatus
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import InternalServerError
from app.domain import OutboxDTO, OutboxRule, CryptoPort

logger = logging.getLogger(__name__)



class OutboxService:
    def __init__(
        self,
        trace_id: str | None,
        uow_factory: Callable[[], UnitOfWork],
        hmac: CryptoPort.TokenHasher,
    ) -> None:
        self._trace_id = trace_id
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
            if outbox_fingerprint is not None:
                outbox_fingerprint = self._hmac.fp_hash(outbox_fingerprint)

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
                ),False
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
                    "app.job.registry.deliver_outbox_event",
                    oid,
                    job_id=f"outbox-{oid}",  # 중복 outbox enqueue 방지
                    retry=None,
                )
                logger.info("enqueued outbox id=%s", oid)

            uow.commit()  #  enqueue까지 성공하면 commit
            return len(ids)

    # @retry(
    #     stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10)
    # )
    def deliver_outbox(self, outbox_id: int, dispatch_fn) -> None:
        attempt_started_at = utcnow()

        with self._uow_factory() as uow:
            row = uow.outboxs.get_by_outbox_id(outbox_id)
            if row is None:
                logger.warning("outboxs not found id=%s", outbox_id)
                return
            if row.status != OutboxStatus.SENDING:
                logger.info("skip id=%s status=%s", outbox_id, row.status)
                return

            payload = OutboxRule.parse_payload(getattr(row, "payload", None))
            attempts = row.attempts + 1
            outbox_filter = OutboxDTO.OutboxFilter(id=row.id)

        # 2) 공통으로 쓸 상태 변수들 미리 선언
        success: bool = False
        retryable: bool = False
        status: OutboxStatus = OutboxStatus.SENDING  # 임시값
        next_run_at: datetime | None = None
        result_code: str | None = None
        result_message: str | None = None
        result_payload: dict[str, Any]

        try:
            send_result = dispatch_fn(event_type=row.event_type, payload=payload)
            if isinstance(send_result, dict):
                # SES raw dict 이면 그대로/부분만 저장
                result_payload = {
                    "provider": "ses",
                    "message_id": send_result.get("MessageId"),
                    "request_id": send_result.get("ResponseMetadata", {}).get(
                        "RequestId"
                    ),
                }
            elif send_result is not None:
                # 문자열(MessageId) 같은 단일 값이면 래핑
                result_payload = {
                    "provider": "ses",
                    "message_id": str(send_result),
                }

            # 성공 케이스
            success = True
            retryable = False
            status = OutboxStatus.SENT
            result_code = "OK"
            result_message = "sent"

        except Exception as e:
            with self._uow_factory() as uow:
                provider = uow.channels.get_channel_by_code("EMAIL")
                policy = provider.retry_policy  # JSON → dict 파싱

                if policy is None:
                    raise InternalServerError(
                        "retry policy not configured",
                        target="channel_provider.retry_policy",
                    )
                max_attempts = policy["max_attempts"]
                base_delay = policy["base_delay_sec"]
                max_delay = policy["max_delay_sec"]

                if attempts < max_attempts:
                    retryable = True
                    status = OutboxStatus.PENDING
                    delay = OutboxRule.compute_backoff(
                        attempts,
                        base_delay_sec=base_delay,
                        max_delay_sec=max_delay,
                    )
                    next_run_at = utcnow() + delay

                    print(
                        f"max_attempts={max_attempts}, base_delay={base_delay}, max_delay={max_delay}, attempts={attempts},  next_at={next_run_at}"
                    )

                else:
                    retryable = False
                    status = OutboxStatus.FAILED

                response = getattr(e, "response", None)
                error = response.get("Error", {}) if isinstance(response, dict) else {}
                result_code = error.get("Code") or e.__class__.__name__
                result_message = error.get("Message") or str(e)
                result_payload = {
                    "provider": "ses",
                    "error_code": result_code,
                    "error_message": result_message,
                }

                logger.exception(
                    "process failed outbox id=%s attempts=%s", row.id, attempts
                )
                uow.commit()
        finally:
            with self._uow_factory() as uow:
                uow.outboxs.add_outbox_attempt(
                    OutboxDTO.OutboxAttemptCreate(
                        outbox_id=outbox_id,
                        attempt_no=attempts,
                        success=1 if success else 0,
                        retryable=1 if retryable else 0,
                        result_code=result_code,
                        result_message=result_message,
                        result_payload=result_payload,
                        started_at=attempt_started_at,
                        finished_at=utcnow(),
                    ),False
                )

                outbox_update = OutboxDTO.OutboxUpdate(
                    attempts=attempts,
                    status=status,
                    next_run_at=next_run_at,
                )
                uow.outboxs.update_outbox_by_filter(
                    filters=outbox_filter,
                    updates=outbox_update,
                )

                uow.commit()
