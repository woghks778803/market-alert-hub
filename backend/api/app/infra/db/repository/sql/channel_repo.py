from typing import Sequence
from sqlalchemy.orm import aliased, Session as DbSession, selectinload
from sqlalchemy import insert, select
from app.infra.db.model import UserChannelModel
from ..protocol.channel_repo import ChannelRepo

class SqlChannelRepo(ChannelRepo): 
    def __init__(self, db: DbSession):
        self._db = db

    def list_by_user(self, user_id: int) -> Sequence[UserChannelModel]:
        stmt = (
            select(UserChannelModel)
            .options(selectinload(UserChannelModel.channel_provider))
            .where(UserChannelModel.user_id == user_id, UserChannelModel.is_valid.is_(True))
            .order_by(UserChannelModel.created_at.desc())
        )
        return self._db.execute(stmt).scalars().all()

    def get_by_id(self, user_channel_id: int) -> UserChannelModel | None:
        stmt = select(UserChannelModel).options(selectinload(UserChannelModel.channel_provider)).where(UserChannelModel.id == user_channel_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def find_one_by_provider_id(
        self, *, user_id: int, provider_id: int,
    ) -> UserChannelModel | None:
        uc = UserChannelModel
        
        stmt = select(uc).where(
            uc.user_id == user_id,
            uc.channel_provider_id == provider_id,
            uc.is_valid.is_(True),
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def add(self, row: UserChannelModel) -> None:
        self._db.add(row)