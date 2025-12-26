from typing import List, Callable
from app.domain.shared.uow import UnitOfWork
from app.domain import CryptoPort
from app.domain import ConflictError, ValidationAppError
from app.infra.db.model import UserChannelModel
from app.core.util.datetime import utcnow
from app.core.util.serialization import to_canonical_json
from app.domain import ChannelRule

class ChannelService:
    def __init__(self, *, uow_factory: Callable[[], UnitOfWork], hmac: CryptoPort.TokenHasher):
        self._uow_factory = uow_factory
        self._hmac = hmac

    # 목록
    def list_channels_by_user_id(self, user_id: int):
        with self._uow_factory() as uow:
            rows = uow.channels.list_channels_by_user_id(user_id)
            return rows

    def get_by_channel_id(self, *, user_channel_id: int):
        with self._uow_factory() as uow:
            return uow.channels.get_by_channel_id(user_channel_id)

    def create_channel(self, *, user_id: int, provider_id: int, config: dict | None):

        with self._uow_factory() as uow:
            chp = uow.providers.get_by_provider_id(provider_id)
            if not chp:
                raise ValidationAppError(
                    "Unknown channel provider.", target="provider_id"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active.", target="provider.is_active"
                )

            channel_cnt = uow.channels.get_channel_cnt(
                user_id=user_id, provider_id=provider_id
            )
            # TODO 현재는 5개 고정 나중에 결제 서비스 넣을때 변경
            if channel_cnt >= ChannelRule.MAX_CHANNELS_PER_USER:
                raise ConflictError(
                    "Channel limit already exceed.", target="provider_id, user_id"
                )

            # provider.user_schema 기반 JSON 검증 훅
            ChannelRule.validate_user_config(
                code=chp.code, config=config, user_schema=chp.user_schema
            )

            fingerprint = to_canonical_json(config)
            if fingerprint is not None: fingerprint= self._hmac.fp_hash(fingerprint)

            existed = uow.channels.get_channel_by_fingerprint(
                user_id=user_id,
                provider_id=provider_id,
                fingerprint=fingerprint,
            )
            if existed:
                raise ConflictError(
                    "Channel with same configuration already exists.",
                    target="user_id, provider_id, fingerprint",
                )

            row = UserChannelModel(
                user_id=user_id,
                channel_provider_id=provider_id,
                config=config or {},
                config_fingerprint=fingerprint,
                is_deleted=False,
            )
            uow.channels.add_channel(row)
            uow.commit()
            # refresh가 UoW에 없다면 session.refresh(row) 호출
            # uow.db.refresh(row)

            result = uow.channels.get_by_channel_id(user_channel_id=row.id)
            return result


    def delete_channel(self, *, user_channel_id: int):
        with self._uow_factory() as uow:
            row = uow.channels.get_by_channel_id(user_channel_id)
            if not row:
                return None
            row.is_deleted = True
            uow.commit()
            return row
