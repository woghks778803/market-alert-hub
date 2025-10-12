from datetime import timedelta
import json, random

MAX_ATTEMPTS = 5

def parse_payload(v) -> dict:
    if v is None: return {}
    if isinstance(v, (bytes, bytearray)):
        v = v.decode("utf-8", errors="ignore")
    if isinstance(v, str):
        try: return json.loads(v)
        except Exception: return {"raw": v}
    if isinstance(v, dict): return v
    return {"value": v}

def compute_backoff(attempts: int) -> timedelta:
    base = min(600, 2 ** max(0, attempts-1))  # 1s, 2s, 4s... capped
    jitter = random.uniform(0, min(5, base * 0.1))
    return timedelta(seconds=base + jitter)