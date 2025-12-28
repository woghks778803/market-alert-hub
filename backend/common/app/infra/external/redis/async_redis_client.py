import logging
from dataclasses import dataclass
from functools import lru_cache
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AsyncRedisClientConfig:
    # 연결/응답 타임아웃 (초)
    connect_timeout: float = 1.5
    socket_timeout: float = 2.5

    # 연결 유지/헬스체크
    health_check_interval: int = 30

    # 명령 실패 시 타임아웃 관련 동작
    retry_on_timeout: bool = True


class AsyncRedisClient:
    def __init__(
        self, redis_url: str, *, cfg: AsyncRedisClientConfig | None = None
    ) -> None:
        self._cfg = cfg or AsyncRedisClientConfig()
        self._client: AsyncRedis = AsyncRedis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=self._cfg.connect_timeout,
            socket_timeout=self._cfg.socket_timeout,
            retry_on_timeout=self._cfg.retry_on_timeout,
            health_check_interval=self._cfg.health_check_interval,
        )

    async def get(self, key: str) -> bytes | None:
        try:
            value = await self._client.get(name=key)
            if value is None:
                return None
            return value
        except RedisError as e:
            log.exception("redis get failed key=%s", key)
            raise

    async def set(
        self,
        key: str,
        value: bytes,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        try:
            res = await self._client.set(name=key, value=value, nx=nx, ex=ex)
            return bool(res)
        except RedisError as e:
            log.exception("redis set failed: key=%s", key)
            raise

    async def delete(self, key: str) -> int:
        try:
            result = await self._client.delete(name=key)
            return result
        except RedisError as e:
            log.exception("redis delete failed: key=%s", key)
            raise

    async def aclose(self) -> None:
        """
        프로세스 종료 시 close 호출하면 커넥션 정리 가능.
        """
        if self._client is None:
            return
        try:
            await self._client.aclose()
        finally:
            self._client = None


@lru_cache
def get_async_redis_client(redis_url: str) -> AsyncRedisClient:
    return AsyncRedisClient(redis_url)
