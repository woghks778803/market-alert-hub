import logging
from dataclasses import dataclass
from functools import lru_cache
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError, ResponseError

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisClientAsyncConfig:
    # 연결/응답 타임아웃 (초)
    connect_timeout: float = 1.5
    socket_timeout: float = 2.5

    # 연결 유지/헬스체크
    health_check_interval: int = 30

    # 명령 실패 시 타임아웃 관련 동작
    retry_on_timeout: bool = True


class RedisClientAsync:
    def __init__(
        self, redis_url: str, *, cfg: RedisClientAsyncConfig | None = None
    ) -> None:
        self._cfg = cfg or RedisClientAsyncConfig()
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

    async def set_value( # set 타입 충돌로 set_value로 네이밍 변경
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

    async def xread(
        self,
        streams: dict[str, str],
        *,
        count: int | None = None,
        block: int | None = None,
    ):
        try:
            return await self._client.xread(
                streams=streams,
                count=count,
                block=block,
            )
        except RedisError:
            log.exception("redis xread failed: streams=%s", streams)
            raise

    async def hset(self, key: str, mapping: dict):
        try:
            return await self._client.hset(name=key, mapping=mapping)
        except RedisError:
            log.exception("redis hset failed: key=%s", key)
            raise

    async def hget(self, key: str, field: str):
        try:
            return await self._client.hget(name=key, key=field)
        except RedisError:
            log.exception("redis hget failed: key=%s field=%s", key, field)
            raise

    async def hdel(self, key: str, *fields: str) -> int:
        try:
            if not fields:
                return 0
            return await self._client.hdel(key, *fields)
        except RedisError:
            log.exception("redis hdel failed: key=%s fields=%s", key, fields)
            raise

    async def hmget(self, key: str, fields: list[str]) -> list[bytes | None]:
        try:
            return await self._client.hmget(name=key, keys=fields)
        except RedisError:
            log.exception("redis hmget failed: key=%s fields=%s", key, fields)
            raise

    async def hgetall(self, key: str) -> dict[bytes, bytes]:
        try:
            result = await self._client.hgetall(name=key)
            return result or {}
        except RedisError as e:
            log.exception("redis hgetall failed: key=%s", key)
            raise

    async def srem(self, key: str, *values: str) -> int:
        try:
            if not values:
                return 0
            return await self._client.srem(key, *values)
        except RedisError:
            log.exception("redis srem failed: key=%s values=%s", key, values)
            raise

    async def smembers(self, key: str) -> set[bytes]:
        try:
            return await self._client.smembers(name=key)
        except RedisError:
            log.exception("redis smembers failed: key=%s", key)
            raise

    async def publish(self, channel: str, message: str) -> int:
        try:
            return await self._client.publish(channel, message)
        except RedisError:
            log.exception("redis publish failed: channel=%s", channel)
            raise

    async def pubsub(self):
        try:
            return self._client.pubsub()
        except RedisError:
            log.exception("redis pubsub create failed")
            raise

    async def psubscribe(self, *patterns: str):
        try:
            pubsub = self._client.pubsub()
            await pubsub.psubscribe(*patterns)
            return pubsub
        except RedisError:
            log.exception("redis psubscribe failed: patterns=%s", patterns)
            raise

    async def xadd(
        self,
        key: str,
        fields: dict[str, str | bytes | int | float],
        *,
        maxlen: int | None = None,
        approximate: bool = True,
    ) -> str:
        try:
            result = await self._client.xadd(
                name=key,
                fields=fields,
                maxlen=maxlen,
                approximate=approximate,
            )
            return str(result)
        except RedisError:
            log.exception("redis xadd failed: key=%s", key)
            raise

    async def xgroup_create(
        self,
        *,
        key: str,
        group_name: str,
        id: str = "0",
        mkstream: bool = True,
    ) -> bool:
        try:
            result = await self._client.xgroup_create(
                name=key,
                groupname=group_name,
                id=id,
                mkstream=mkstream,
            )
            return bool(result)

        except ResponseError:
            raise
        except RedisError:
            log.exception("redis xgroup_create failed: key=%s", key)
            raise


    async def xreadgroup(
        self,
        *,
        group_name: str,
        consumer_name: str,
        streams: dict[str, str],
        count: int,
        block_ms: int,
    ):
        try:
            result = await self._client.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams=streams,
                count=count,
                block=block_ms,
            )
            return result
        except RedisError:
            log.exception("redis xreadgroup failed: streams=%s", streams)
            raise


    async def xack(self, key: str, group_name: str, *message_ids: str) -> int:
        try:
            result = await self._client.xack(key, group_name, *message_ids)
            return int(result)
        except RedisError:
            log.exception("redis xack failed: key=%s", key)
            raise


    def pipeline(self, transaction: bool = True):
        try:
            return self._client.pipeline(transaction=transaction)
        except RedisError:
            log.exception("redis pipeline create failed")
            raise

    def conn(self) -> AsyncRedis:
        return self._client

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
def get_async_redis_client(redis_url: str) -> RedisClientAsync:
    return RedisClientAsync(redis_url)
