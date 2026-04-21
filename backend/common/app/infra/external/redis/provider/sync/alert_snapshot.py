import json
from typing import Any

from app.core.constants import ALERTS, SNAP, OutboxEventType
from app.domain import AlertPort
from app.infra.external.redis.redis_client import RedisClient


class RedisAlertSnapshot(AlertPort.AlertSnapshot):
    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def alert_upsert(self, alert_id: int, payload: dict[str, Any], ttl_sec: int | None = None) -> None:
        """
        단일 알림 Redis snapshot 반영
        """
        redis_key = self._snapshot_key()

        value = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        pipe = self._redis.pipeline()
        pipe.hset(redis_key, str(alert_id), value)

        if ttl_sec and ttl_sec > 0:
            pipe.expire(redis_key, ttl_sec)

        pipe.execute()

    def alert_remove(self, alert_id: int) -> None:
        """
        단일 알림 Redis snapshot 제거
        """
        redis_key = self._snapshot_key()
        self._redis.hdel(redis_key, str(alert_id))

    def alert_get(self, alert_id: int) -> dict[str, Any] | None:
        redis_key = self._snapshot_key()
        raw = self._redis.hget(redis_key, str(alert_id))

        if not raw:
            return None

        if isinstance(raw, bytes):
            raw = raw.decode()

        data = json.loads(raw)
        return data if isinstance(data, dict) else None

    def _snapshot_key(self) -> str:
        return f"{self._prefix}:{SNAP}:{OutboxEventType.SYNC_ALERTS.value}"
