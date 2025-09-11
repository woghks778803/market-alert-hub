import os
from backend.worker.queue.redis_streams import Streams


def streams():
    return Streams(
        host=os.getenv("REDIS_HOST", "redis"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        stream=os.getenv("REDIS_STREAM_ALERTS", "alerts"),
    )
