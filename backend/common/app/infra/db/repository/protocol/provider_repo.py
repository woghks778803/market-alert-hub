from typing import Protocol
from app.infra.db.model import ChannelProviderModel

class ProviderRepo(Protocol):
    def get_by_provider_id(self, provider_id: int) -> ChannelProviderModel | None: ...
    def get_provider_by_code(self, code: str) -> ChannelProviderModel | None: ...

