from typing import Protocol, Any, Mapping


class RuntimePort:
    class Kv(Protocol):
        """
        최소 Key-Value 계약 (sync).
        - value는 bytes로 고정해서 직렬화 정책은 호출자가 선택
        """

        def get(self, key: str) -> bytes | None: ...
        def set(self, key: str, value: bytes, *, ttl_sec: int | None = None) -> None: ...
        def delete(self, key: str) -> int: ...
        def ttl(self, key: str) -> int | None: ...
        def set_if_absent(self, key: str, value: bytes, *, ttl_sec: int) -> bool: ...

    class AsyncKv(Protocol):
        """
        최소 Key-Value 계약 (async).
        collector 같은 async 루프에서만 사용.
        """

        async def get(self, key: str) -> bytes | None: ...
        async def set(self, key: str, value: bytes, *, ttl_sec: int | None = None) -> None: ...
        async def delete(self, key: str) -> int: ...
        async def ttl(self, key: str) -> int | None: ...
        async def set_if_absent(self, key: str, value: bytes, *, ttl_sec: int) -> bool: ...

    class Queue(Protocol):
        """
        최소 큐 계약.
        RQ든 다른 큐든 '밀어넣기'만 표현.
        """

        def enqueue(
            self,
            task_name: str,
            *,
            args: tuple[Any, ...] = (),
            kwargs: Mapping[str, Any] | None = None,
            job_timeout_sec: int | None = None,
        ) -> str: ...

    class Worker(Protocol):
        """
        최소 워커 계약.
        """

        def work(self) -> None: ...
        def request_stop(self) -> None: ...
