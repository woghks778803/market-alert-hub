
from app.core.constants import StreamType, STREAM
from app.domain import OutboxPort
from app.infra.external.redis.async_redis_client import RedisClientAsync


class RedisOutboxEvent(OutboxPort.AsyncOutboxEvent):
    def __init__(
        self,
        redis: RedisClientAsync,
        prefix: str
    ) -> None:
        self._redis = redis
        self._stream_key = f"{prefix}:{STREAM}:{StreamType.PERSIST_OUTBOX_EVENTS.value}"

    async def add_event(self, outbox_id: int) -> str:
        message_id = await self._redis.xadd(
            self._stream_key,
            {
                "outbox_id": str(outbox_id),
            },
        )
        return message_id.decode() if isinstance(message_id, bytes) else message_id