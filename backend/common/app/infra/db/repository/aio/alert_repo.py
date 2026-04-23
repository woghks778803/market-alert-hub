from typing import Sequence
from datetime import datetime
from sqlalchemy import update, insert, select, and_, or_, asc, desc, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import AlertStatus, AlertSort
from app.domain import AlertDTO
from app.infra.db.model import AlertModel, AlertTypeModel, ExchangeInstrumentModel, ExchangeModel, UserModel
from app.infra.db.repository.protocol.aio.alert_repo import AlertRepo

a = AlertModel
at = AlertTypeModel
e = ExchangeModel
ei = ExchangeInstrumentModel
u = UserModel

class AsyncAlertRepo(AlertRepo):
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_alert_summary(
        self,
        *,
        user_id: int,
        deleted_is_null: bool = True,
    ) -> AlertDTO.AlertSummary: ...