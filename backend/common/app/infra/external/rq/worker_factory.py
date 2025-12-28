from dataclasses import dataclass
from typing import Any, Callable, Sequence
from rq import Worker


@dataclass(frozen=True)
class RqWorkerConfig:
    name: str = "worker"
    with_scheduler: bool = True
    log_job_description: bool = True


class RqWorkerFactory:
    """
    - wiring에서 Worker(...) 직접 호출 금지
    """

    def __init__(
        self,
        redis_conn_provider: Callable[[], Any],
        *,
        cfg: RqWorkerConfig | None = None
    ) -> None:
        self._redis_conn_provider = redis_conn_provider
        self._cfg = cfg or RqWorkerConfig()

    def build(self, queues: Sequence[Any]):

        conn = self._redis_conn_provider()
        return Worker(
            queues,
            connection=conn,
            name=self._cfg.name,
            log_job_description=self._cfg.log_job_description,
        )

    def work(self, worker: Any) -> None:
        worker.work(with_scheduler=self._cfg.with_scheduler)

    def request_stop(self, worker: Any, signum: int, frame: Any) -> None:
        # pylance가 request_stop(sig, frame) 요구하는 케이스 대응
        worker.request_stop(signum=signum, frame=frame)
