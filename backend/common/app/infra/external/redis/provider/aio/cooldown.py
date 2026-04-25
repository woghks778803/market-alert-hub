from app.core.constants import CooldownType, COOLDOWN
from app.domain import ThrottlePort
from app.infra.external.redis.async_redis_client import RedisClientAsync


class RedisCooldown(ThrottlePort.Cooldown):

    def __init__(self, redis: RedisClientAsync, prefix: str):
        self._redis = redis
        self._prefix = prefix

    async def acquire_alert_price(self, alert_id: int, ttl_sec: int) -> bool:
        return await self._acquire(
            self._alert_price_key(alert_id),
            ttl_sec,
        )

    async def remain_alert_price(self, alert_id: int) -> int:
        return await self._remain(
            self._alert_price_key(alert_id),
        )

    async def _acquire(self, key: str, ttl_sec: int) -> bool:
        if ttl_sec <= 0:
            return True

        redis_key = self._redis_key(key)

        result = await self._redis.set_value(
            redis_key,
            b"1",
            nx=True,
            ex=ttl_sec,
        )

        return bool(result)

    async def _remain(self, key: str) -> int:
        redis_key = self._redis_key(key)

        ttl = await self._redis.ttl(redis_key)

        return ttl if ttl > 0 else 0

    def _alert_price_key(self, alert_id: int) -> str:
        return f"{CooldownType.ALERT_PRICE.value}:{alert_id}"
        
    def _redis_key(self, key: str) -> str:
        return f"{self._prefix}:{COOLDOWN}:{key}"