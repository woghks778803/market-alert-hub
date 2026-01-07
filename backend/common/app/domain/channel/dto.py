from dataclasses import dataclass, asdict
from datetime import datetime
from app.core.constants import OutboxStatus
from typing import Optional, Iterable, Any


@dataclass(slots=True)
class UserChannel:
    id: int
    user_id: int
    channel_provider_id: int
    address: str | None
    config: dict | None
    config_fingerprint: bytes | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    is_default: bool
    is_deleted: bool


@dataclass(slots=True)
class ChannelProvider:
    id: int
    code: str
    name: str
    description: str | None

    user_schema: dict | None
    admin_schema: dict | None
    rate_limit_policy: dict | None
    retry_policy: dict | None

    is_active: bool
    created_at: datetime
    updated_at: datetime