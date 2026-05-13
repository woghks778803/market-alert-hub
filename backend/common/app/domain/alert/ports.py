from typing import Protocol, Any
from decimal import Decimal
from collections.abc import Collection, Mapping

class MessageBuilder(Protocol):
    def build_body(
        self,
        *,
        context: dict[str, object],
        trigger_value: Decimal | None,
    ) -> str:
        raise NotImplementedError

class AlertSnapshot(Protocol):
    def upsert_alert(self, alert_id: int, payload: dict[str, Any], ttl_sec: int | None = None) -> None:
        raise NotImplementedError

    def remove_alert(self, alert_id: int) -> None:
        raise NotImplementedError

    def get_alert(self, alert_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

class AlertBucket(Protocol):
    def add_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
        ttl_sec: int | None = None,
    ) -> None:
        raise NotImplementedError

    def remove_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
    ) -> None:
        raise NotImplementedError

    def get_alert_bucket_key(
        self,
        *,
        indicator: str,
        exchange_code: str,
        exchange_symbol: str,
        form_type: str,
        scope: str,
        direction: str,
    ) -> str:
        raise NotImplementedError

class AsyncAlertSnapshot(Protocol):
    async def get_alert(self, alert_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    async def mget_alert(self, alert_ids: list[int]) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def remove_alert(self, alert_id: int) -> None:
        raise NotImplementedError

    async def remove_alerts(self, alert_ids: Collection[int]) -> None:
        raise NotImplementedError

class AsyncAlertBucket(Protocol):
    async def list_alert_id(self, *, bucket_key: str) -> list[int]: 
        raise NotImplementedError
        
    async def list_alert_ids(self, *, bucket_keys: list[str]) -> list[int]:
        raise NotImplementedError

    async def remove_alerts_by_bucket(
        self,
        items: Mapping[str, Collection[int]],
    ) -> None:
        raise NotImplementedError

class AsyncAlertEvent(Protocol):
    async def add_event(self, payload: dict[str, Any]) -> str:
        raise NotImplementedError


    async def add_events(self, payloads: list[dict[str, Any]]) -> list[str]:
        raise NotImplementedError


    async def read_persist_alert_events(
        self,
        *,
        consumer_name: str,
        count: int,
        block_ms: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        raise NotImplementedError


    async def ack_persist_alert_events(
        self,
        *,
        message_ids: list[str],
    ) -> int:
        raise NotImplementedError


    async def ensure_persist_group(self) -> None:
        raise NotImplementedError