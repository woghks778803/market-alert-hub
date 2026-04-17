import json
from typing import Any

from app.core.constants import ALERTS, PRICE, BUCKET, INDEX, OutboxEventType
from app.domain import AlertPort
from app.infra.external.redis.redis_client import RedisClient

class RedisAlertBucket(AlertPort.AlertBucket):
    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def _alert_add(
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

    def _alert_remove(
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

    def _list_alert_ids(
        self,
        *,
        bucket_key: str,
    ) -> list[int]:
        """
        bucket에 포함된 alert_id 목록 조회
        """
        redis_key = self._bucket_key(bucket_key)
        rows = self._redis.smembers(redis_key)

        result: list[int] = []
        for row in rows:
            try:
                if isinstance(row, bytes):
                    row = row.decode()

                result.append(int(row))
            except (TypeError, ValueError):
                continue

        return result

    def alert_add_price(
        self,
        *,
        exchange_code: str,
        exchange_symbol: str,
        alert_id: int,
        ttl_sec: int | None = None,
    ) -> None:
        bucket_key = self.get_price_bucket_key(exchange_code, exchange_symbol)
        self._alert_add(bucket_key=bucket_key, alert_id=alert_id, ttl_sec=ttl_sec)

    def alert_remove_price(
        self,
        *,
        exchange_code: str,
        exchange_symbol: str,
        alert_id: int,
    ) -> None:
        bucket_key = self.get_price_bucket_key(exchange_code, exchange_symbol)
        self._alert_remove(bucket_key=bucket_key, alert_id=alert_id)

    def list_price_alert_ids(
        self,
        *,
        exchange_code: str,
        exchange_symbol: str,
    ) -> list[int]:
        bucket_key = self.get_price_bucket_key(
            exchange_code=exchange_code,
            exchange_symbol=exchange_symbol,
        )
        return self._list_alert_ids(bucket_key=bucket_key)

    def get_price_bucket_key(self, exchange_code: str, exchange_symbol: str) -> str:
        return f"{PRICE}:{exchange_code}:{exchange_symbol}"

    def _bucket_index_key(self) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{INDEX}"

    def _bucket_key(self, bucket_key: str) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{bucket_key}"