from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.infra.db.repository.protocol.aio.alert_repo import AlertRepo
from app.infra.db.repository.protocol.aio.outbox_repo import OutboxRepo
from app.infra.db.repository.aio.alert_repo import AsyncAlertRepo
from app.infra.db.repository.aio.outbox_repo import AsyncOutboxRepo

class AsyncUnitOfWork:
    def __init__(
        self,
        db: Union[AsyncSession, async_sessionmaker[AsyncSession]],
        owns_session: bool = True,
    ) -> None:
        self.db: AsyncSession = db() if callable(db) else db

        self._alerts = None
        self._outboxs = None

        self._done = False
        self._owns = owns_session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, *_):
        if not self.db:
            return False
            
        try:
            if exc_type and not self._done:
                await self.db.rollback()
        finally:
            if self._owns:
                await self.db.close()
        return False

    async def commit(self) -> None:
        if not self._done:
            await self.db.commit()
            self._done = True

    async def rollback(self) -> None:
        if not self._done:
            await self.db.rollback()
            self._done = True
    
    async def flush(self) -> None:
        if self._done:
            return
        await self.db.flush()

    @property
    def alerts(self) -> AlertRepo:
        if self._alerts is None:
            self._alerts = AsyncAlertRepo(self.db)
        return self._alerts

    @property
    def outboxs(self) -> OutboxRepo:
        if self._outboxs is None:
            self._outboxs = AsyncOutboxRepo(self.db)
        return self._outboxs