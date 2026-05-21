from typing import Protocol, Sequence
from app.domain import ChannelDTO
from app.infra.db.model import UserChannelModel, ChannelProviderModel

class ChannelRepo(Protocol): 
    def list_provider_by_filter(
        self,
        *,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[ChannelDTO.ChannelProvider]: ...
    def get_provider_by_code(self, code: str, is_active: bool = True) -> ChannelDTO.ChannelProvider | None: ...
    def get_by_channel_id(self, user_channel_id: int) -> ChannelDTO.UserChannel | None: ...
    def get_channel_cnt(
        self, 
        *, 
        user_id: int, 
        provider_id: int, 
        is_active: bool, 
        deleted_is_null: bool = True,
    ) -> int: ...

    def update_channel_active(
        self,
        channel_provider_id: int,
        is_active: bool,
        user_id: int | None = None,
        address: str | None = None,
    ) -> int: ...
    def upsert_channel(
        self,
        *,
        row: ChannelDTO.UserChannelCreate
    ) -> None: ...