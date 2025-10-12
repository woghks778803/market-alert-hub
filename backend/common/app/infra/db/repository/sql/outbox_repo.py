from sqlalchemy import select, update, func
from sqlalchemy.orm import Session as DbSession
from app.core.constants import OutboxStatus
from app.infra.db.model import OutboxModel
from ..protocol.outbox_repo import OutboxRepo

class SqlOutboxRepo(OutboxRepo):
    def __init__(self, db: DbSession):
        self.db = db

    def add(self, row: OutboxModel) -> None:
        self.db.add(row)

    def get(self, id: int) -> OutboxModel | None:
        return self.db.execute(select(OutboxModel).where(OutboxModel.id == id)).scalar_one_or_none()

    def mark_inflight(self, ids: list[int]):
        if not ids:
            return
        self.db.execute(
            update(OutboxModel)
            .where(OutboxModel.id.in_(ids))
            .values(status=OutboxStatus.SENDING)
        )

    def mark_sent(self, id: int, attempts: int):
        self.db.execute(
            update(OutboxModel)
            .where(OutboxModel.id == id)
            .values(status=OutboxStatus.SENT, attempts=attempts + 1, error_msg=None)
        )

    def mark_pending(self, id: int, attempts: int, next_at, err: str) -> None:
        self.db.execute(
            update(OutboxModel)
            .where(OutboxModel.id == id)
            .values(
                status=OutboxStatus.PENDING,
                attempts=attempts,
                next_attempt_at=next_at,
                error_msg=err,
            )
        )
        
    def mark_failed(self, id: int, attempts: int, err: str):
        self.db.execute(
            update(OutboxModel)
            .where(OutboxModel.id == id)
            .values(status=OutboxStatus.FAILED, attempts=attempts, error_msg=err)
        )

    def due_pending_ids(self, limit: int) -> list[int]:
        rows = self.db.execute(
            select(OutboxModel.id)
            .where(OutboxModel.status == OutboxStatus.PENDING)
            .order_by(OutboxModel.id)
            .limit(limit)
        ).scalars().all()
        return list(rows)
