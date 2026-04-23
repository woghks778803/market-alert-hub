from typing import Protocol, Any

class AlertSnapshot(Protocol):
    def alert_upsert(self, alert_id: int, payload: dict[str, Any], ttl_sec: int | None = None) -> None:
        raise NotImplementedError

    def alert_remove(self, alert_id: int) -> None:
        raise NotImplementedError

    def alert_get(self, alert_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

class AlertBucket(Protocol):
    def alert_add_price(
        self,
        *,
        exchange_code: str,
        exchange_symbol: str,
        alert_id: int,
        ttl_sec: int | None = None,
    ) -> None:
        raise NotImplementedError

    def alert_remove_price(
        self,
        *,
        exchange_code: str,
        exchange_symbol: str,
        alert_id: int,
    ) -> None:
        raise NotImplementedError

    def get_price_bucket_key(exchange_code: str, exchange_symbol: str) -> str:
        raise NotImplementedError

class AsyncAlertSnapshot(Protocol):
    async def alert_get(self, alert_id: int) -> dict[str, Any] | None:
        raise NotImplementedError

    async def alert_mget(self, alert_ids: list[int]) -> list[dict[str, Any]]:
        raise NotImplementedError


class AsyncAlertBucket(Protocol):
    async def list_alert_id(self, *, bucket_key: str) -> list[int]: 
        raise NotImplementedError
        
    async def list_alert_id_many(self, *, bucket_keys: list[str]) -> list[int]:
        raise NotImplementedError