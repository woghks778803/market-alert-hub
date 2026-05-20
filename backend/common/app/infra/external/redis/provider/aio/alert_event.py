import json
from typing import Any
from redis.exceptions import ResponseError

from app.core.constants import StreamType, ALERTS, STREAM
from app.core.util.serialization import json_safe, decode_bytes, decode_bytes_dict
from app.domain import AlertPort
from app.infra.external.redis.async_redis_client import RedisClientAsync


class RedisAlertEvent(AlertPort.AsyncAlertEvent):

    def __init__(self, redis: RedisClientAsync, prefix: str):
        self._redis = redis
        self._prefix = prefix

    async def read_persist_alert_events(
        self,
        *,
        consumer_name: str,
        count: int,
        block_ms: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        return await self._read_events(
            group_name=StreamType.PERSIST_ALERT_EVENTS.value,
            consumer_name=consumer_name,
            stream_key=self._stream_key(),
            stream_id=">",
            count=count,
            block_ms=block_ms,
        )
    
    async def ack_persist_alert_events(
        self,
        *,
        message_ids: list[str],
    ) -> int:
        return await self._ack_events(
            group_name=StreamType.PERSIST_ALERT_EVENTS.value,
            message_ids=message_ids,
        )

    async def ensure_persist_group(self) -> None:
        await self._ensure_group(
            group_name=StreamType.PERSIST_ALERT_EVENTS.value,
        )

    async def add_event(self, payload: dict[str, Any]) -> str:
        message_id = await self._redis.xadd(
            self._stream_key(),
            self._to_stream_payload(payload),
            maxlen=10_000,
            approximate=True,
        )

        return str(message_id)

    async def add_events(self, payloads: list[dict[str, Any]]) -> list[str]:
        message_ids: list[str] = []

        for payload in payloads:
            message_id = await self.add_event(payload)
            message_ids.append(message_id)

        return message_ids

    async def _ensure_group(self, *, group_name: str) -> None:
        try:
            await self._redis.xgroup_create(
                key=self._stream_key(),
                group_name=group_name,
                id="0",
                mkstream=True,
            )
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                return
            raise

    async def _read_events(
        self,
        *,
        group_name: str,
        consumer_name: str,
        stream_key: str,
        stream_id: str,
        count: int,
        block_ms: int,
    ) -> list[tuple[str, dict[str, Any]]]:
        result = await self._redis.xreadgroup(
            group_name=group_name,
            consumer_name=consumer_name,
            streams={stream_key: stream_id},
            count=count,
            block_ms=block_ms,
        )

        messages: list[tuple[str, dict[str, Any]]] = []

        for _, stream_messages in result:
            for message_id, fields in stream_messages:
                # byte면 decode 필요 "b'1746840000000-0'"
                messages.append(
                    (str(decode_bytes(message_id)), decode_bytes_dict(fields))
                )

        return messages


    async def _ack_events(
        self,
        *,
        group_name: str,
        message_ids: list[str],
    ) -> int:
        if not message_ids:
            return 0

        return await self._redis.xack(
            self._stream_key(),
            group_name,
            *message_ids,
        )
    
    def _to_stream_payload(self, payload: dict[str, Any]) -> dict[str, str]:
        return {
            "p": json.dumps(
                json_safe(payload),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        }
    
    def _stream_key(self) -> str:
        return f"{self._prefix}:{STREAM}:{StreamType.PERSIST_ALERT_EVENTS.value}"