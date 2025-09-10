import json, redis


class Streams:
    def __init__(self, host: str, port: int, stream: str):
        self.r = redis.Redis(host=host, port=port, decode_responses=True)
        self.stream = stream

    def publish(self, payload: dict):
        return self.r.xadd(self.stream, {"data": json.dumps(payload)})

    def consume(self, group: str, consumer: str, block_ms: int = 2000):
        try:
            return self.r.xreadgroup(
                group, consumer, {self.stream: ">"}, count=10, block=block_ms
            )
        except redis.exceptions.ResponseError:
            self.r.xgroup_create(self.stream, group, id="$", mkstream=True)
            return []
