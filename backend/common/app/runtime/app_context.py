from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class AppContext:
    svcs: Any
    redis_conn: Any
