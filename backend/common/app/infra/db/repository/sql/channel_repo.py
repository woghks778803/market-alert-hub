from typing import Sequence
from sqlalchemy.orm import aliased, Session as DbSession, selectinload
from sqlalchemy import insert, select, func, and_
from app.infra.db.model import UserChannelModel
from ..protocol.channel_repo import ChannelRepo

class SqlChannelRepo(ChannelRepo): 
    def __init__(self, db: DbSession):
        self._db = db

    def list_channels_by_user_id(self, user_id: int) -> Sequence[UserChannelModel]:
        stmt = (
            select(UserChannelModel)
            .options(selectinload(UserChannelModel.channel_provider))
            .where(UserChannelModel.user_id == user_id, UserChannelModel.is_deleted.is_(False))
            .order_by(UserChannelModel.created_at.desc())
        )
        return self._db.execute(stmt).scalars().all()

    def get_by_channel_id(self, user_channel_id: int) -> UserChannelModel | None:
        stmt = select(UserChannelModel).options(selectinload(UserChannelModel.channel_provider)).where(UserChannelModel.id == user_channel_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_channel_cnt(
        self, *, user_id: int, provider_id: int,
    ) -> int:
        uc = UserChannelModel
        
        stmt = select(func.count(uc.id)).where(
            uc.user_id == user_id,
            uc.channel_provider_id == provider_id,
            uc.is_deleted.is_(False),
        )
        return self._db.execute(stmt).scalar()

    def get_channel_by_fingerprint(
        self, *, user_id: int, provider_id: int, fingerprint: bytes | None
    ) -> UserChannelModel:
        uc = UserChannelModel
        stmt = (
        select(uc)
            .where(
                and_(
                    uc.user_id == user_id,
                    uc.channel_provider_id == provider_id,
                    uc.config_fingerprint == fingerprint,
                    uc.is_deleted.is_(False),  # 살아있는 것만
                )
            )
            .limit(1)
        )

        return self._db.execute(stmt).scalar()
        

    def add_channel(self, row: UserChannelModel) -> None:
        self._db.add(row)