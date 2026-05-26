import logging
from typing import cast
from dataclasses import dataclass
from functools import lru_cache

from redis.client import Redis as SyncRedis, Pipeline
from redis.cluster import RedisCluster as SyncRedisCluster
from redis.exceptions import RedisError, ResponseError

from .shared.dto import RedisClientConfig

log = logging.getLogger(__name__)


class RedisClient:
    """
    redis-py 래퍼. (infra/external 전용)
    - decode_responses=False 기본(바이트 기반)
    - 쿨다운/락 등 간단 KV 사용 목적
    """

    def __init__(self, redis_url: str, *, config: RedisClientConfig | None = None) -> None:
        self._config = config or RedisClientConfig()

        common_kwargs = dict(
            decode_responses=False,
            socket_connect_timeout=self._config.connect_timeout,
            socket_timeout=self._config.socket_timeout,
            health_check_interval=self._config.health_check_interval,
        )

        if self._config.cluster_enabled:
            self._client = SyncRedisCluster.from_url(
                redis_url,
                ssl_check_hostname=False,
                **common_kwargs,
            )
        else:
            self._client = SyncRedis.from_url(
                redis_url,
                retry_on_timeout=self._config.retry_on_timeout,
                **common_kwargs,
            )


    def set_value( # set 타입 충돌로 set_value로 네이밍 변경
        self,
        key: str,
        value: bytes,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        """
        redis SET wrapper
        - nx=True : NX
        - ex  : EX seconds
        returns: True if key was set, False otherwise
        """
        try:
            ok = self._client.set(name=key, value=value, nx=nx, ex=ex)
            return bool(ok)
        except RedisError:
            log.exception("redis set failed: key=%s", key)
            raise

    def ttl(self, key: str) -> int:
        """
        returns:
          >=0 : TTL seconds
          -1  : key exists but has no expire
          -2  : key does not exist
        """
        try:
            return cast(int, self._client.ttl(key))
        except RedisError:
            log.exception("redis ttl failed: key=%s", key)
            raise

    def incr(self, key: str) -> int:
        try:
            return int(self._client.incr(key))
        except RedisError:
            log.exception("redis incr failed: key=%s", key)
            raise


    def expire(self, key: str, ttl_sec: int) -> bool:
        try:
            ok = self._client.expire(key, ttl_sec)
            return bool(ok)
        except RedisError:
            log.exception("redis expire failed: key=%s ttl_sec=%s", key, ttl_sec)
            raise

    def delete(self, key: str) -> int:
        try:
            return cast(int, self._client.delete(key))
        except RedisError:
            log.exception("redis delete failed: key=%s", key)
            raise

    def rename(self, source: str, target: str) -> bool:
        try:
            ok = self._client.rename(source, target)
            return bool(ok)
        except RedisError:
            log.exception(
                "redis rename failed: source=%s target=%s",
                source,
                target,
            )
            raise

    def hget(self, key: str, field: str) -> int:
        try:
            return cast(int, self._client.hget(name=key, key=field))
        except RedisError:
            log.exception("redis hget failed: key=%s field=%s", key, field)
            raise

    def hset(self, key: str, mapping: dict) -> int:
        try:
            return cast(int, self._client.hset(name=key, mapping=mapping))
        except RedisError:
            log.exception("redis hset failed: key=%s", key)
            raise

    # *fields = tuple[str, str....]
    def hdel(self, key: str, *fields: str) -> int:
        try:
            if not fields:
                return 0
            return cast(int, self._client.hdel(key, *fields))
        except RedisError:
            log.exception("redis hdel failed: key=%s fields=%s", key, fields)
            raise

    def hgetall(self, key: str) -> dict[bytes, bytes]:
        try:
            return cast(dict, self._client.hgetall(name=key))
        except RedisError:
            log.exception("redis hgetall failed: key=%s", key)
            raise


    def sadd(self, key: str, *values: str) -> int:
        try:
            if not values:
                return 0
            return cast(int, self._client.sadd(key, *values))
        except RedisError:
            log.exception("redis sadd failed: key=%s values=%s", key, values)
            raise


    def srem(self, key: str, *values: str) -> int:
        try:
            if not values:
                return 0
            return cast(int, self._client.srem(key, *values))
        except RedisError:
            log.exception("redis srem failed: key=%s values=%s", key, values)
            raise


    def smembers(self, key: str) -> set[bytes]:
        try:
            return cast(set[bytes], self._client.smembers(key))
        except RedisError:
            log.exception("redis smembers failed: key=%s", key)
            raise


    def publish(self, channel: str, message: str) -> int:
        try:
            return cast(int, self._client.publish(channel, message))
        except RedisError:
            log.exception("redis publish failed: channel=%s", channel)
            raise


    def xautoclaim(
        self,
        *,
        key: str,
        group_name: str,
        consumer_name: str,
        min_idle_time_ms: int,
        start_id: str = "0-0",
        count: int = 10,
    ):
        try:
            return self._client.xautoclaim(
                name=key,
                groupname=group_name,
                consumername=consumer_name,
                min_idle_time=min_idle_time_ms,
                start_id=start_id,
                count=count,
            )
        except RedisError:
            log.exception("redis xautoclaim failed: key=%s", key)
            raise


    def xgroup_create(
        self,
        *,
        key: str,
        group_name: str,
        id: str = "0",
        mkstream: bool = True,
    ) -> bool:
        try:
            result = self._client.xgroup_create(
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


    def xreadgroup(
        self,
        *,
        group_name: str,
        consumer_name: str,
        streams: dict[str, str],
        count: int,
        block_ms: int,
    ):
        try:
            result = self._client.xreadgroup(
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


    def xack(self, key: str, group_name: str, *message_ids: str) -> int:
        try:
            result = self._client.xack(key, group_name, *message_ids)
            return int(result)
        except RedisError:
            log.exception("redis xack failed: key=%s", key)
            raise


    def conn(self) -> SyncRedis | SyncRedisCluster:
        return self._client


    def pipeline(self, transaction: bool = True) -> Pipeline:
        """
        redis pipeline wrapper

        사용 예:
            pipe = redis.pipeline()
            pipe.get(key)
            pipe.delete(key)
            raw, _ = pipe.execute()
        """
        try:
            return self._client.pipeline(transaction=transaction)
        except RedisError:
            log.exception("redis pipeline create failed")
            raise


# 프로세스 내 재사용(bootstrap이 깔끔해짐)
@lru_cache
def get_redis_client(
    redis_url: str,
    config: RedisClientConfig | None = None,
) -> RedisClient:
    return RedisClient(
        redis_url,
        config=config,
    )
