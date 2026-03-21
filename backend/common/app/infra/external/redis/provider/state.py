import json
import secrets

from app.core.constants import STATE
from app.core.util.datetime import utcnow
from app.domain import AuthPort
from app.infra.external.redis.redis_client import RedisClient


class RedisState(AuthPort.AuthState):

    def __init__(self, redis: RedisClient):
        self._redis = redis

    def create(self, key: str, data: dict, ttl_sec: int = 300) -> str:
        """
        state 생성

        data: state에 저장할 payload
        ttl_sec: state TTL
        """

        state = secrets.token_urlsafe(32)
        redis_key = f"{STATE}:{key}:{state}"

        value_dict = {
            **data,
            "created_at": utcnow().timestamp(),
        }

        value = json.dumps(value_dict).encode()

        ok = self._redis.set(redis_key, value, nx=True, ex=ttl_sec)

        if not ok:
            raise RuntimeError("state_create_failed")

        return state

    def consume(self, key: str, state: str) -> dict | None:
        """
        state 조회 + 삭제 (one-time token)
        """

        redis_key = f"{STATE}:{key}:{state}"

        pipe = self._redis.pipeline()
        pipe.get(redis_key)
        pipe.delete(redis_key)

        raw, _ = pipe.execute()

        if raw is None:
            return None

        return json.loads(raw.decode())
