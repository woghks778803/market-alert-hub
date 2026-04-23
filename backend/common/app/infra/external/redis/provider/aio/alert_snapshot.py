import json
from typing import Any

from app.core.constants import OutboxEventType, SNAP
from app.infra.external.redis.async_redis_client import RedisClientAsync
from app.domain import AlertPort

class RedisAlertSnapshot(AlertPort.AsyncAlertSnapshot):
    def __init__(self, redis: RedisClientAsync, prefix: str):
        self._redis = redis
        self._prefix = prefix

    async def alert_get(self, alert_id: int) -> dict[str, Any] | None:
        """
        단일 알림 Redis snapshot 조회
        """
        redis_key = self._snapshot_key()
        raw = await self._redis.hget(redis_key, str(alert_id))

        if not raw:
            return None

        if isinstance(raw, bytes):
            raw = raw.decode()

        data = json.loads(raw)
        return data if isinstance(data, dict) else None

    async def alert_mget(self, alert_ids: list[int]) -> list[dict[str, Any]]:
        """
        알림 Redis snapshot 다건 조회
        """
        if not alert_ids:
            return []

        redis_key = self._snapshot_key()
        fields = [str(alert_id) for alert_id in alert_ids]

        rows = await self._redis.hmget(redis_key, fields)

        result: list[dict[str, Any]] = []

        for raw in rows:
            if not raw:
                continue

            if isinstance(raw, bytes):
                raw = raw.decode()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if isinstance(data, dict):
                result.append(data)

        return result

    def _snapshot_key(self) -> str:
        return f"{self._prefix}:{SNAP}:{OutboxEventType.SYNC_ALERTS.value}"