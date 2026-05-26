from app.core.constants import CooldownType, COOLDOWN
from app.domain import ThrottlePort
from app.infra.external.redis.redis_client import RedisClient


class RedisCooldown(ThrottlePort.Cooldown):

    def __init__(self, redis: RedisClient, prefix: str):
        self._redis = redis
        self._prefix = prefix

    def incr_exchange_candle_rate_limit(self, exchange_code: str, ttl_sec: int) -> int:
        return self._incr(self._exchange_candle_rate_limit_key(exchange_code), ttl_sec)

    def acquire_email_verify_resend(self, user_id: int, ttl_sec: int) -> bool:
        return self._acquire(self._email_verify_resend_key(user_id), ttl_sec)

    def remain_email_verify_resend(self, user_id: int) -> int:
        return self._remain(self._email_verify_resend_key(user_id))

    def acquire_notice_view(self, key: str, ttl_sec: int) -> bool:
        return self._acquire(self._notice_view_key(key), ttl_sec)

    def acquire_notice_view_rate(self, client_ip: str, ttl_sec: int) -> bool:
        return self._acquire(self._notice_view_rate_key(client_ip), ttl_sec)

    def _incr(self, key: str, ttl_sec: int) -> int:
        redis_key = self._redis_key(key)

        count = self._redis.incr(redis_key)

        if count == 1:
            self._redis.expire(redis_key, ttl_sec)

        return count

    def _acquire(self, key: str, ttl_sec: int) -> bool:
        redis_key = self._redis_key(key)

        return bool(self._redis.set_value(redis_key, b"1", nx=True, ex=ttl_sec))

    def _remain(self, key: str) -> int:
        redis_key = self._redis_key(key)

        ttl = self._redis.ttl(redis_key)
        return ttl if ttl > 0 else 0

    def _exchange_candle_rate_limit_key(self, exchange_code: str) -> str:
        return f"{CooldownType.EXCHANGE_CANDLE_RATE_LIMIT.value}:{exchange_code}"

    def _email_verify_resend_key(self, user_id: int) -> str:
        return f"{CooldownType.EMAIL_VERIFY_RESEND.value}:{user_id}"

    def _notice_view_key(self, key: str) -> str:
        return f"{CooldownType.NOTICE_VIEW.value}:{key}"

    def _notice_view_rate_key(self, client_ip: str) -> str:
        return f"{CooldownType.NOTICE_VIEW_RATE.value}:{client_ip}"

    def _redis_key(self, key: str) -> str:
        return f"{self._prefix}:{COOLDOWN}:{key}"

    