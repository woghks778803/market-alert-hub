from dataclasses import dataclass, asdict
from datetime import datetime
from app.core.constants import OutboxStatus
from typing import Iterable, Any


@dataclass(slots=True)
class UserChannel:
    id: int
    user_id: int
    channel_provider_id: int
    address: str | None
    config: dict | None
    config_hash: bytes | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    is_active: bool

@dataclass(slots=True)
class UserChannelCreate:
    user_id: int
    channel_provider_id: int
    address: str | None
    config: dict | None
    config_hash: bytes | None
    verified_at: datetime | None
    deleted_at: datetime | None
    is_active: bool

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

@dataclass(frozen=True)
class ChannelMessage:
    target: str
    title: str
    body: str
    data: dict[str, str] | None = None

@dataclass(frozen=True)
class ChannelMessageResult:
    success: bool
    message_id: str | None = None
    error: str | None = None

@dataclass(slots=True, frozen=True)
class ChannelSendItem:
    delivery_id: int
    message: ChannelMessage