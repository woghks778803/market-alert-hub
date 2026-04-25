import json
from typing import Any

from app.core.constants import ALERTS, PRICE, BUCKET, INDEX, OutboxEventType
from app.domain import AlertPort
from app.infra.external.redis.redis_client import RedisClient

class RedisAlertBucket(AlertPort.AlertBucket):
    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def _add_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
        ttl_sec: int | None = None,
    ) -> None:
        """
        알림 ID를 Redis bucket에 추가
        """
        redis_key = self._bucket_key(bucket_key)
        index_key = self._bucket_index_key()

        pipe = self._redis.pipeline()
        pipe.sadd(redis_key, str(alert_id))
        pipe.sadd(index_key, bucket_key)

        if ttl_sec and ttl_sec > 0:
            pipe.expire(redis_key, ttl_sec)

        pipe.execute()

    def _remove_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
    ) -> None:
        """
        Redis bucket에서 알림 ID 제거
        """
        redis_key = self._bucket_key(bucket_key)
        self._redis.srem(redis_key, str(alert_id))

    def add_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
        ttl_sec: int | None = None,
    ) -> None:
        self._add_alert(
            bucket_key=bucket_key,
            alert_id=alert_id,
            ttl_sec=ttl_sec,
        )

    def remove_alert(
        self,
        *,
        bucket_key: str,
        alert_id: int,
    ) -> None:
        self._remove_alert(
            bucket_key=bucket_key,
            alert_id=alert_id,
        )

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
        # form_type_key = form_type or "none"
        # scope_key = scope or "none"
        # direction_key = direction or "none"

        return (
            f"{indicator}:{exchange_code}:{exchange_symbol}:"
            f"{form_type}:{scope}:{direction}"
        )

    def _bucket_index_key(self) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{INDEX}"

    def _bucket_key(self, bucket_key: str) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{bucket_key}"