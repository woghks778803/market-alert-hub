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

    def _bucket_key(self, bucket_key: str) -> str:
        return f"{self._prefix}:{BUCKET}:{OutboxEventType.SYNC_ALERTS.value}:{bucket_key}"