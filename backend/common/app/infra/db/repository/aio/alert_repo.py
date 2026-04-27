from typing import Sequence
from datetime import datetime
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO
from app.infra.db.model import AlertModel, AlertTypeModel, AlertEventModel, ExchangeInstrumentModel, ExchangeModel, UserModel
from app.infra.db.repository.protocol.aio.alert_repo import AlertRepo
from app.infra.db.utils import to_row_dict

a = AlertModel
at = AlertTypeModel
ae = AlertEventModel
e = ExchangeModel
ei = ExchangeInstrumentModel
u = UserModel

class AsyncAlertRepo(AlertRepo):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def upsert_alert_events(
        self,
        events: Sequence[AlertDTO.AlertEventCreate],
        *,
        chunk_size: int = 1000,
    ) -> int:
        total = 0

        if not events:
            return total

        for i in range(0, len(events), chunk_size):
            chunk = events[i : i + chunk_size]
            values = [to_row_dict(r) for r in chunk]

            stmt = mysql_insert(ae).values(values)

            # 중복 발생 후 실행할 update 내용
            stmt = stmt.on_duplicate_key_update(
                id=ae.id, # 중복이면 수정 무시
            )

            result = await self._db.execute(stmt)

            total += int(result.rowcount or 0)

        return total