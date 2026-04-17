import logging
from dataclasses import dataclass
from functools import lru_cache

from redis.client import Redis as SyncRedis, Pipeline
from redis.exceptions import RedisError
from typing import cast

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class RedisClientConfig:
    # 연결/응답 타임아웃 (초)
    connect_timeout: float = 1.5
    socket_timeout: float = 2.5

    # 연결 유지/헬스체크
    health_check_interval: int = 30

    # 명령 실패 시 타임아웃 관련 동작
    retry_on_timeout: bool = True


class RedisClient:
    """
    redis-py 래퍼. (infra/external 전용)
    - decode_responses=False 기본(바이트 기반)
    - 쿨다운/락 등 간단 KV 사용 목적
    """

    def __init__(self, redis_url: str, *, cfg: RedisClientConfig | None = None) -> None:
        self._cfg = cfg or RedisClientConfig()
        self._client: SyncRedis = SyncRedis.from_url(
            redis_url,
            decode_responses=False,
            socket_connect_timeout=self._cfg.connect_timeout,
            socket_timeout=self._cfg.socket_timeout,
            retry_on_timeout=self._cfg.retry_on_timeout,
            health_check_interval=self._cfg.health_check_interval,
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

    def delete(self, key: str) -> int:
        try:
            return cast(int, self._client.delete(key))
        except RedisError:
            log.exception("redis delete failed: key=%s", key)
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

    def hdel(self, key: str, *fields: str) -> int:
        try:
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
            log.exception("redis sadd failed: key=%s", key)
            raise


    def srem(self, key: str, *values: str) -> int:
        try:
            if not values:
                return 0
            return cast(int, self._client.srem(key, *values))
        except RedisError:
            log.exception("redis srem failed: key=%s", key)
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

    def conn(self) -> SyncRedis:
        return self._client

    def pipeline(self) -> Pipeline:
        """
        redis pipeline wrapper

        사용 예:
            pipe = redis.pipeline()
            pipe.get(key)
            pipe.delete(key)
            raw, _ = pipe.execute()
        """
        try:
            return self._client.pipeline()
        except RedisError:
            log.exception("redis pipeline create failed")
            raise

    # def set_cooldown(self, key: str, *, ttl_sec: int) -> bool:
    #     """
    #     NX + EX ttl
    #     """
    #     return self.set(key, b"1", nx=True, ex=ttl_sec)

    # def get_retry_after_sec(self, key: str, *, fallback: int) -> int:
    #     """
    #     ttl이 애매한 값(-1/-2)이면 fallback 반환.
    #     """
    #     t = self.ttl(key)
    #     if t > 0:
    #         return t
    #     return fallback


# 프로세스 내 재사용(bootstrap이 깔끔해짐)
@lru_cache
def get_redis_client(redis_url: str) -> RedisClient:
    return RedisClient(redis_url)
