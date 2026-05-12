import logging
from typing import Callable

from app.core.util.datetime import utcnow
from app.core.constants import OutboxStatus
from app.domain import OutboxDTO, OutboxPort
from app.domain.shared.async_uow import AsyncUnitOfWork

logger = logging.getLogger(__name__)

class OutboxService:
    def __init__(
        self, 
        uow_factory: Callable[[], AsyncUnitOfWork],
        outbox_event: OutboxPort.OutboxEvent
    ) -> None:
        self._uow_factory = uow_factory
        self._outbox_event = outbox_event


    async def enqueue_outbox_pending(self, limit: int) -> int:
        async with self._uow_factory() as uow:
            outbox_filter = OutboxDTO.OutboxFilter(
                status=OutboxStatus.PENDING,
                next_run_at=utcnow(),
            )
            ids = await uow.outboxs.list_outbox_by_filter(
                outbox_filter,
                limit=limit,
            )
            if not ids:
                return 0

            await uow.outboxs.update_outbox_by_filter(
                filters=OutboxDTO.OutboxFilter(ids=ids),
                updates=OutboxDTO.OutboxUpdate(
                    status=OutboxStatus.SENDING,
                ),
            )

            await uow.commit()

        stream_added_ids: list[int] = []

        # 보상 트랜잭션 - add_event 실패시 sending outbox 상태 변경
        try:
            for outbox_id in ids:
                await self._outbox_event.add_event(outbox_id)
                stream_added_ids.append(outbox_id)
                logger.info("added outbox stream event id=%s", outbox_id)

            return len(stream_added_ids)

        except Exception:
            failed_ids = [outbox_id for outbox_id in ids if outbox_id not in stream_added_ids]

            if failed_ids:
                async with self._uow_factory() as uow:
                    await uow.outboxs.update_outbox_by_filter(
                        filters=OutboxDTO.OutboxFilter(ids=failed_ids),
                        updates=OutboxDTO.OutboxUpdate(
                            status=OutboxStatus.PENDING,
                        ),
                    )
                    await uow.commit()

            raise