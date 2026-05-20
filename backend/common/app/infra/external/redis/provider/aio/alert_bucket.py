from collections.abc import Collection, Mapping

from app.core.constants import OutboxEventType, BUCKET
from app.domain import AlertPort
from app.infra.external.redis.async_redis_client import RedisClientAsync

class RedisAlertBucket(AlertPort.AsyncAlertBucket):
    def __init__(self, redis: RedisClientAsync, prefix: str):
        self._redis = redis
        self._prefix = prefix

    async def list_alert_id(self, *, bucket_key: str) -> list[int]:
        """
        bucket에 포함된 alert_id 목록 조회
        """
        redis_key = self._bucket_key(bucket_key)
        rows = await self._redis.smembers(redis_key)

        result: list[int] = []

        for row in rows:
            try:
                if isinstance(row, bytes):
                    row = row.decode()

                result.append(int(row))
            except (TypeError, ValueError):
                continue

        return result

    async def list_alert_ids(self, *, bucket_keys: list[str]) -> list[int]:
        """
        여러 bucket의 alert_id 목록 조회
        """
        if not bucket_keys:
            return []

        pipe = self._redis.pipeline(transaction=False)

        for bucket_key in bucket_keys:
            redis_key = self._bucket_key(bucket_key)
            pipe.smembers(redis_key)

        rows_list = await pipe.execute()

        alert_ids: set[int] = set()

        for rows in rows_list:
            if not rows:
                continue

            for row in rows:
                try:
                    if isinstance(row, bytes):
                        row = row.decode()

                    alert_ids.add(int(row))
                except (TypeError, ValueError):
                    continue

        return list(alert_ids)

    async def remove_alerts_by_bucket(
        self,
        items: Mapping[str, Collection[int]],
    ) -> None:
        """
        bucket_key별 alert_id bulk 제거

        items 예:
        {
            "price:UPBIT:KRW-BTC:...": [1, 2, 3],
            "price:BINANCE:BTCUSDT:...": [4, 5],
        }
        """
        if not items:
            return

        pipe = self._redis.pipeline(transaction=False)

        for bucket_key, alert_ids in items.items():
            if not alert_ids:
                continue

            redis_key = self._bucket_key(bucket_key)
            values = [str(alert_id) for alert_id in set(alert_ids)]

            if values:
                pipe.srem(redis_key, *values)

        await pipe.execute()


    def _bucket_key(self, bucket_key: str) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{bucket_key}"