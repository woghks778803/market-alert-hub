from typing import List, Callable
from app.service.uow import UnitOfWork
from app.domain import ConflictError, ValidationAppError
from app.infra.db.model import UserChannelModel
from app.core.datetime_utils import utcnow
from app.domain import ChannelRule 

class ChannelService:
    def __init__(
            self,
            *, 
            uow_factory: Callable[[], UnitOfWork]
        ):
        self._uow_factory = uow_factory


    # 목록
    def list(self, user_id: int):
        with self._uow_factory() as uow:
            rows = uow.channels.list_by_user(user_id)
            return rows  

    # 생성
    def create(self, *, user_id: int, provider_id: int, config: dict | None):
        
        with self._uow_factory() as uow:
            chp = uow.providers.get_by_id(provider_id)
            if not chp:
                raise ValidationAppError("Unknown channel provider.", target="provider_id")
            if not chp.is_active:
                raise ValidationAppError("Channel provider is not active.", target="provider.is_active")

            existed = uow.channels.find_one_by_provider_id(user_id=user_id, provider_id=provider_id)
            if existed:
                raise ConflictError("Channel already exists for provider.", target="provider_id, user_id")

            # (선택) provider.user_schema 기반 JSON 검증 훅
            ChannelRule.validate_user_config(code=chp.code, config=config, user_schema=chp.user_schema)

            row = UserChannelModel(
                user_id=user_id,
                channel_provider_id=provider_id,
                config=config or {},
                is_valid=True,
            )
            uow.channels.add(row)
            uow.commit()
            # refresh가 UoW에 없다면 session.refresh(row) 호출
            uow.db.refresh(row)

            result = uow.channels.get_by_id(user_channel_id=row.id)
            return result

    # (옵션) 검증 완료 마킹
    def mark_verified(self, *, user_channel_id: int):
        with self._uow_factory() as uow:
            repo = uow.channels
            row = repo.get_by_id(user_channel_id)
            if not row or not row.is_valid:
                raise ValidationAppError("Channel not found or invalid.")
            row.verified_at = utcnow()
            uow.commit()
            return row

    # (옵션) 비활성화
    def delete_channel(self, *, user_channel_id: int):
        with self._uow_factory() as uow:
            repo = uow.channels
            row = repo.get_by_id(user_channel_id)
            if not row:
                return None
            row.is_valid = False
            uow.commit()
            return row

    

