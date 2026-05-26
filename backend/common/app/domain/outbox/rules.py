from datetime import timedelta
import json, random

MAX_ATTEMPTS = 5


def compute_backoff(
    attempts: int,
    *,
    base_delay_sec: int,
    max_delay_sec: int,
) -> timedelta:
    # attempts: 1 → base_delay, 2 → base_delay*2, 3 → base_delay*4 ...
    n = max(0, attempts - 1)
    delay = base_delay_sec * (2**n)
    delay = min(delay, max_delay_sec)
    return timedelta(seconds=delay)
