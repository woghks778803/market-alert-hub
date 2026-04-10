from typing import Callable
from app.core.constants import ChannelCode
from app.core.util.serialization import to_canonical_json
from app.core.util.datetime import utcnow, ensure_utc
from app.infra.db.model import UserChannelModel
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
    def list_channel_by_filter(self, limit: int, offset: int):
        with self._uow_factory() as uow:
            rows = uow.channels.list_channel_by_filter(limit=limit, offset=offset)
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
                user_id=user_id, provider_id=provider_id
            )
            # TODO 현재는 5개 고정 나중에 결제 서비스 넣을때 변경
            if channel_cnt >= ChannelRule.MAX_CHANNELS_PER_USER:
                raise ConflictError(
                    "Channel limit already exceed", target="user_channel"
                )

            # provider.user_schema 기반 JSON 검증 훅
            ChannelRule.validate_user_config(
                code=chp.code, config=config, user_schema=chp.user_schema
            )

            token_hash = to_canonical_json(config)
            if token_hash is not None:
                token_hash = self._hmac.to(token_hash)

            uow.channels.update_channel_active(
                channel_provider_id=provider.id,
                address=token,
                is_active=False
            )

            uow.channels.upsert_channel(
                ChannelDTO.UserChannelCreate(
                    user_id=user_id,
                    channel_provider_id=provider.id,
                    address=token,
                    config=config,
                    config_hash=token_hash,
                    verified_at=now,
                    deleted_at=None,
                    is_active=True
                )
            )

            uow.commit()

            return {"ok": True}
            

    def deactivate_channel(self, *, user_id: int, code: ChannelCode, config: dict) -> None:
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
                code=chp.code, config=config, user_schema=chp.user_schema
            )

            uow.channels.update_channel_active(
                user_id=user_id,
                channel_provider_id=chp.id,
                address=token,
                is_active=False,
            )

            uow.commit()
