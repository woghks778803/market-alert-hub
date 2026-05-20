from redis.exceptions import ResponseError

from app.core.constants import StreamType, STREAM
from app.domain import OutboxPort, OutboxDTO
from app.infra.external.redis.redis_client import RedisClient

class RedisOutboxEvent(OutboxPort.OutboxEvent):
    def __init__(
        self,
        redis: RedisClient,
        prefix: str,
    ):
        self._redis = redis
        self._prefix = prefix

    def claim_persist_outbox_events(
        self,
        *,
        consumer_name: str,
        min_idle_time_ms: int,
        count: int,
    ) -> list[OutboxDTO.OutboxMessage]:
        result = self._redis.xautoclaim(
            key=self._stream_key(),
            group_name=StreamType.PERSIST_OUTBOX_EVENTS.value,
            consumer_name=consumer_name,
            min_idle_time_ms=min_idle_time_ms,
            start_id="0-0",
            count=count,
        )

        _, entries, *_ = result

        messages: list[OutboxDTO.OutboxMessage] = []

        for message_id, fields in entries:
            raw_outbox_id = fields.get(b"outbox_id")
            if raw_outbox_id is None:
                continue

            messages.append(
                OutboxDTO.OutboxMessage(
                    message_id=(
                        message_id.decode()
                        if isinstance(message_id, bytes)
                        else message_id
                    ),
                    outbox_id=int(raw_outbox_id),
                )
            )

        return messages

    def read_persist_outbox_events(
        self,
        *,
        consumer_name: str,
        count: int,
        block_ms: int,
    ) -> list[OutboxDTO.OutboxMessage]:
        return self._read_events(
            group_name=StreamType.PERSIST_OUTBOX_EVENTS.value,
            consumer_name=consumer_name,
            stream_key=self._stream_key(),
            stream_id=">",
            count=count,
            block_ms=block_ms,
        )

    def ack_persist_outbox_events(
        self,
        *,
        message_ids: list[str],
    ) -> int:
        return self._ack_events(
            group_name=StreamType.PERSIST_OUTBOX_EVENTS.value,
            message_ids=message_ids,
        )

    def ensure_persist_group(self) -> None:
        self._ensure_group(
            group_name=StreamType.PERSIST_OUTBOX_EVENTS.value,
        )

    def _ensure_group(self, *, group_name: str) -> None:
        try:
            self._redis.xgroup_create(
                key=self._stream_key(),
                group_name=group_name,
                id="0",
                mkstream=True,
            )
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                return
            raise

    def _read_events(
        self,
        *,
        group_name: str,
        consumer_name: str,
        stream_key: str,
        stream_id: str,
        count: int = 1,
        block_ms: int = 5000,
    ) -> list[OutboxDTO.OutboxMessage]:
        result = self._redis.xreadgroup(
            group_name=group_name,
            consumer_name=consumer_name,
            streams={stream_key: stream_id},
            count=count,
            block_ms=block_ms,
        )

        messages: list[OutboxDTO.OutboxMessage] = []

        for _, stream_messages in result:
            for message_id, fields in stream_messages:
                raw_outbox_id = fields.get(b"outbox_id")
                if raw_outbox_id is None:
                    continue

                messages.append(
                    OutboxDTO.OutboxMessage(
                        message_id=(
                            message_id.decode()
                            if isinstance(message_id, bytes)
                            else message_id
                        ),
                        outbox_id=int(raw_outbox_id),
                    )
                )

        return messages

    def _ack_events(
        self,
        *,
        group_name: str,
        message_ids: list[str],
    ) -> int:
        if not message_ids:
            return 0

        return self._redis.xack(
            self._stream_key(),
            group_name,
            *message_ids,
        )

    def _stream_key(self) -> str:
        return f"{self._prefix}:{STREAM}:{StreamType.PERSIST_OUTBOX_EVENTS.value}"