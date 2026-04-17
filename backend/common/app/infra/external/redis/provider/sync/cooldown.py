from app.core.constants import COOLDOWN
from app.domain import ThrottlePort
from app.infra.external.redis.redis_client import RedisClient


class RedisCooldown(ThrottlePort.Cooldown):

    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def acquire(self, key: str, ttl_sec: int) -> bool:
        redis_key = f"{self._prefix}:{COOLDOWN}:{key}"

        return bool(self._redis.set(redis_key, b"1", nx=True, ex=ttl_sec))

    def remain(self, key: str) -> int:
        redis_key = f"{self._prefix}:{COOLDOWN}:{key}"

        ttl = self._redis.ttl(redis_key)
        return ttl if ttl > 0 else 0
