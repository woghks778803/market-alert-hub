from dataclasses import dataclass
from typing import Any, Callable, Optional
from rq import Queue


@dataclass(frozen=True)
class RqQueueConfig:
    default_timeout: Optional[int] = None
    is_async: bool = True  # 테스트에서 False 쓰고 싶으면 옵션으로


class RqQueueFactory:
    """
    - wiring에서 Queue(...) 직접 호출 금지
    """

    def __init__(
        self,
        redis_conn_provider: Callable[[], Any],
        *,
        cfg: RqQueueConfig | None = None
    ) -> None:
        self._redis_conn_provider = redis_conn_provider
        self._cfg = cfg or RqQueueConfig()

    def queue(self, name: str):

        conn = self._redis_conn_provider()
        return Queue(
            name,
            connection=conn,
            default_timeout=self._cfg.default_timeout,
            is_async=self._cfg.is_async,
        )
