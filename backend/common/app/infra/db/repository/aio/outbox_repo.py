from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain import OutboxDTO
from app.domain.shared.errors import ValidationAppError
from app.infra.db.model import OutboxModel
from app.infra.db.repository.common.outbox import to_outbox_where_mapping, to_outbox_values_mapping
from app.infra.db.repository.protocol.aio.outbox_repo import OutboxRepo
from app.infra.db.utils import to_row_dict


class AsyncOutboxRepo(OutboxRepo):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db


    async def update_outbox_by_filter(
        self,
        filters: OutboxDTO.OutboxFilter,
        updates: OutboxDTO.OutboxUpdate,
    ) -> int:
        where = to_outbox_where_mapping(filters)
        if not where:
            raise ValidationAppError(
                "Unsafe update: at least one narrowing filter required",
                target="filters",
            )

        values = to_outbox_values_mapping(updates)
        if not values:
            return 0

        result = await self._db.execute(
            update(OutboxModel)
            .where(*where)
            .values(values)
            .execution_options(synchronize_session=False)
        )

        return int(getattr(result, "rowcount", 0) or 0)


    async def list_outbox_by_filter(
        self,
        filters: OutboxDTO.OutboxFilter,
        *,
        limit: int | None = None,
        offset: int = 0,
        order_desc: bool = False,
        for_update: bool = False,
        skip_locked: bool = False,
    ) -> list[int]:
        where = to_outbox_where_mapping(filters)

        stmt = (
            select(OutboxModel.id)
            .where(*where)
            .order_by(
                OutboxModel.id.desc()
                if order_desc
                else OutboxModel.id.asc()
            )
        )

        if for_update:
            stmt = stmt.with_for_update(skip_locked=skip_locked)
        if offset:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        rows = (await self._db.execute(stmt)).scalars().all()
        return list(rows)