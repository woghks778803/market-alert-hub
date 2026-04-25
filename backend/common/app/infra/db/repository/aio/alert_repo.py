from typing import Sequence
from datetime import datetime
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO
from app.infra.db.model import AlertModel, AlertTypeModel, AlertEventModel, ExchangeInstrumentModel, ExchangeModel, UserModel
from app.infra.db.repository.protocol.aio.alert_repo import AlertRepo

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
    ) -> int:
        if not events:
            return 0

        rows = [
            {
                "alert_id": event.alert_id,
                "exchange_instrument_id": event.exchange_instrument_id,
                "status": event.status,
                "detected_at": event.detected_at,
                "queued_at": event.queued_at,
                "trigger_value": event.trigger_value,
                "context": event.context,
                "dedup_key": event.dedup_key,
            }
            for event in events
        ]

        stmt = mysql_insert(ae).values(rows)

        # 중복 발생 후 실행할 update 내용
        stmt = stmt.on_duplicate_key_update(
            id=ae.id, # 중복이면 수정 무시
        )

        result = await self._db.execute(stmt)

        return int(result.rowcount or 0)