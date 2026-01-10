from sqlalchemy import select, update, func
from sqlalchemy.orm import Session as DbSession

from app.domain import OutboxDTO
from app.domain.shared.errors import ValidationAppError
from app.infra.db.model import OutboxModel, OutboxAttemptModel
from ..protocol.outbox_repo import OutboxRepo


class SqlOutboxRepo(OutboxRepo):
    def __init__(self, db: DbSession):
        self._db = db

    def add_outbox(
        self, row: OutboxDTO.OutboxCreate, is_flush: bool
    ) -> OutboxDTO.Outbox:
        outbox = OutboxModel.from_create_dto(row)
        self._db.add(outbox)
        if is_flush:
            self._db.flush()
        return outbox.to_dto()

    def add_outbox_attempt(
        self, row: OutboxDTO.OutboxAttemptCreate, is_flush: bool
    ) -> OutboxDTO.OutboxAttempt:
        outbox_attempt = OutboxAttemptModel.from_create_dto(row)
        self._db.add(outbox_attempt)
        if is_flush:
            self._db.flush()
        return outbox_attempt.to_dto()

    def get_by_outbox_id(self, id: int) -> OutboxDTO.Outbox | None:
        outbox: OutboxModel | None = (
            self._db.execute(select(OutboxModel).where(OutboxModel.id == id))
            .scalars()
            .one_or_none()
        )
        if outbox is None:
            return None
        return outbox.to_dto()

    def _to_outbox_where_mapping(self, outbox_filter: OutboxDTO.OutboxFilter):
        wheres = []

        if outbox_filter.id is not None:
            wheres.append(OutboxModel.id == outbox_filter.id)
        elif outbox_filter.ids:
            wheres.append(OutboxModel.id.in_(outbox_filter.ids))  # [] 방지

        if outbox_filter.next_run_at is not None:
            wheres.append(OutboxModel.next_run_at < outbox_filter.next_run_at)
        if outbox_filter.status is not None:
            wheres.append(OutboxModel.status == outbox_filter.status)

        return wheres

    def _to_outbox_values_mapping(self, outbox_update: OutboxDTO.OutboxUpdate):
        values = {}

        if outbox_update.status is not None:
            values[OutboxModel.status] = outbox_update.status
        if outbox_update.attempts is not None:
            values[OutboxModel.attempts] = outbox_update.attempts
        if outbox_update.next_run_at is not None:
            values[OutboxModel.next_run_at] = outbox_update.next_run_at

        return values

    def update_outbox_by_filter(
        self, filters: OutboxDTO.OutboxFilter, updates: OutboxDTO.OutboxUpdate
    ) -> int:

        where = self._to_outbox_where_mapping(filters)
        if not where:
            raise ValidationAppError(
                "Unsafe update: at least one narrowing filter required",
                target="filters",
            )
        values = self._to_outbox_values_mapping(updates)
        if not values:
            return 0

        result = self._db.execute(
            update(OutboxModel)
            .where(*where)
            .values(values)
            .execution_options(synchronize_session=False)
        )

        return int(getattr(result, "rowcount", 0) or 0)

    def list_outboxs_by_filter(
        self,
        filters: OutboxDTO.OutboxFilter,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_desc: bool = False,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[int]:

        where = self._to_outbox_where_mapping(filters)
        stmt = (
            select(OutboxModel.id)
            .where(*where)
            .order_by(OutboxModel.id.desc() if order_desc else OutboxModel.id.asc())
        )

        if for_update:
            stmt = stmt.with_for_update(skip_locked=skip_locked)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        rows = self._db.execute(stmt).scalars().all()
        return list(rows)
