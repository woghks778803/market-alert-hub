from typing import Callable
from app.core.constants import ChannelCode
from app.core.util.serialization import to_canonical_json
from app.core.util.datetime import utcnow
from app.domain.shared.uow import UnitOfWork
from app.domain.shared.errors import ConflictError, ValidationAppError, NotFoundError
from app.domain import CryptoPort, ChannelRule, ChannelDTO

class ChannelService:
    def __init__(
        self, *, uow_factory: Callable[[], UnitOfWork], hmac: CryptoPort.TokenHasher
    ):
        self._uow_factory = uow_factory
        self._hmac = hmac

    # 목록
    def list_provider_by_filter(self, is_active: bool | None, limit: int, offset: int):
        with self._uow_factory() as uow:
            rows = uow.channels.list_provider_by_filter(is_active=is_active, limit=limit, offset=offset)
            return rows

    def get_by_channel_id(self, *, user_channel_id: int):
        with self._uow_factory() as uow:
            return uow.channels.get_by_channel_id(user_channel_id)

    def register_channel(self, *, user_id: int, code: ChannelCode, config: dict):
        now = utcnow()

        with self._uow_factory() as uow:
            chp = uow.channels.get_provider_by_code(code)
            if not chp:
                raise NotFoundError(
                    "Not found channel provider", target="channel_provider"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active", target="channel_provider"
                )

            channel_cnt = uow.channels.get_channel_cnt(
                user_id=user_id, provider_id=chp.id, is_active=True
            )
            
            # TODO 현재는 5개 고정 나중에 결제 서비스 넣을때 변경
            if channel_cnt >= ChannelRule.MAX_ACTIVE_CHANNELS_PER_USER:
                raise ConflictError(
                    "Channel limit already exceed", target="user_channel"
                )

            # chp.user_schema 기반 JSON 검증 훅
            ChannelRule.validate_user_config(
                code=ChannelCode(chp.code), config=config, user_schema=chp.user_schema
            )

            config_hash = to_canonical_json(config)
            if config_hash is not None:
                config_hash = self._hmac.token_hash(config_hash)

            uow.channels.update_channel_active(
                channel_provider_id=chp.id,
                address=config.get("token"),
                is_active=False
            )

            uow.channels.upsert_channel(
                row=ChannelDTO.UserChannelCreate(
                    user_id=user_id,
                    channel_provider_id=chp.id,
                    address=config.get("token"),
                    config=config,
                    config_hash=config_hash,
                    verified_at=now,
                    deleted_at=None,
                    is_active=True
                )
            )

            uow.commit()

            return {"ok": True}
            

    def deactivate_channel(self, *, code: ChannelCode, config: dict) -> None:
        with self._uow_factory() as uow:
            chp = uow.channels.get_provider_by_code(code)
            if not chp:
                raise NotFoundError(
                    "Not found channel provider", target="channel_provider"
                )
            if not chp.is_active:
                raise ValidationAppError(
                    "Channel provider is not active", target="channel_provider"
                )

            ChannelRule.validate_user_config(
                code=ChannelCode(chp.code), config=config, user_schema=chp.user_schema
            )

            uow.channels.update_channel_active(
                channel_provider_id=chp.id,
                address=config.get("token"),
                is_active=False,
            )

            uow.commit()
