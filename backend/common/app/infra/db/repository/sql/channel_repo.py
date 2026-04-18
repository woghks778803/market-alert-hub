from typing import Sequence
from sqlalchemy.orm import aliased, Session as DbSession, selectinload
from sqlalchemy import update, insert, select, func, and_, asc, desc
from sqlalchemy.dialects.mysql import insert as mysql_insert
from app.domain import ChannelDTO
from app.domain.shared.errors import ValidationAppError
from app.infra.db.model import UserChannelModel, ChannelProviderModel
from app.infra.db.repository.protocol.channel_repo import ChannelRepo
from app.infra.db.utils import to_row_dict

class SqlChannelRepo(ChannelRepo): 
    def __init__(self, db: DbSession):
        self._db = db

    def list_channel_by_filter(
        self,
        *,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ChannelDTO.ChannelProvider]:
        stmt = (
            select(ChannelProviderModel)
            .where(
                and_(
                    ChannelProviderModel.is_active.is_(is_active),
                )
            )
            .order_by(asc(ChannelProviderModel.id))
            .limit(limit)
            .offset(offset)
        )

        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def get_provider_by_code(self, code: str, is_active: bool = True) -> ChannelDTO.ChannelProvider | None:
        stmt = (
            select(ChannelProviderModel)
            .where(
                ChannelProviderModel.code == code, 
                ChannelProviderModel.is_active.is_(is_active)
            )
        )
        provider = self._db.execute(stmt).scalars().one_or_none()

        if provider is None:
            return None
        return provider.to_dto()

    def get_by_channel_id(self, user_channel_id: int) -> UserChannelModel | None:
        stmt = select(UserChannelModel).options(selectinload(UserChannelModel.channel_provider)).where(UserChannelModel.id == user_channel_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_channel_by_code(self, code: str) -> ChannelProviderModel:
        stmt = select(ChannelProviderModel).where(ChannelProviderModel.code == code)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_channel_cnt(
        self, 
        *, 
        user_id: int, 
        provider_id: int,
        is_active: bool,
        deleted_is_null: bool = True,
    ) -> int | None:
        uc = UserChannelModel
        
        stmt = select(func.count(uc.id)).where(
            uc.user_id == user_id,
            uc.channel_provider_id == provider_id,
            uc.is_active.is_(is_active),
        )

        if deleted_is_null:
            stmt = stmt.where(uc.deleted_at.is_(None))

        return self._db.execute(stmt).scalar()

    def update_channel_active(
        self,
        channel_provider_id: int,
        is_active: bool,
        user_id: int | None = None,
        address: str | None = None,
    ) -> int:
        if user_id is None and address is None:
            raise ValidationAppError(
                "Unsafe update: at least one narrowing filter required",
                target="filters",
            )

        wheres = [
            UserChannelModel.channel_provider_id == channel_provider_id,
            UserChannelModel.deleted_at.is_(None)
        ]

        if user_id is not None:
            wheres.append(UserChannelModel.user_id == user_id)

        if address is not None:
            wheres.append(UserChannelModel.address == address)

        stmt = (
            update(UserChannelModel)
            .where(*wheres)
            .values(is_active=is_active)
        )

        result = self._db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    def upsert_channel(
        self,
        *,
        row: ChannelDTO.UserChannelCreate
    ) -> None:
        row_dict = to_row_dict(row)
        stmt = mysql_insert(UserChannelModel).values(**row_dict)
        stmt = stmt.on_duplicate_key_update(
            user_id=stmt.inserted.user_id,
            channel_provider_id=stmt.inserted.channel_provider_id,
            address=stmt.inserted.address,
            config=stmt.inserted.config,
            config_hash=stmt.inserted.config_hash,
            verified_at=stmt.inserted.verified_at,
            is_active=stmt.inserted.is_active,
            deleted_at=stmt.inserted.deleted_at,
        )

        self._db.execute(stmt)


            