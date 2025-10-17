from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import ChannelProviderModel
from ..protocol.provider_repo import ProviderRepo

class SqlProviderRepo(ProviderRepo):
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_by_provider_id(self, provider_id: int) -> ChannelProviderModel | None:
        stmt = select(ChannelProviderModel).where(ChannelProviderModel.id == provider_id)
        return self._db.execute(stmt).scalar_one_or_none()
    
    def get_provider_by_code(self, code: str) -> ChannelProviderModel | None:
        stmt = select(ChannelProviderModel).where(ChannelProviderModel.code == code)
        return self._db.execute(stmt).scalar_one_or_none()

