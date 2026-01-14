from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    text: str

    def json(self) -> Any:
        import json

        return json.loads(self.text)


class SyncHttpTransport(Protocol):
    def get(
        self, path: str, *, params: dict[str, Any] | None = None
    ) -> HttpResponse: ...
    def close(self) -> None: ...
