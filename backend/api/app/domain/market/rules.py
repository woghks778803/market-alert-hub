from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from random import Random
from app.core.constants import CandleBaseInterval
from app.domain.errors import ValidationAppError

# Interval = Literal["1m","5m","15m","1h","4h","1d","1w","1M"]

# def _floor(ts: datetime, out: Interval) -> datetime:
#     ts = ts.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
#     if out.endswith("m"):
#         m = int(out[:-1]); return ts.replace(second=0, microsecond=0, minute=(ts.minute//m)*m)
#     if out.endswith("h"):
#         h = int(out[:-1]); return ts.replace(minute=0, second=0, microsecond=0, hour=(ts.hour//h)*h)
#     if out == "1d":
#         return ts.replace(hour=0, minute=0, second=0, microsecond=0)
#     if out == "1w":
#         d = (ts.isoweekday()-1) % 7
#         base = ts - timedelta(days=d)
#         return base.replace(hour=0, minute=0, second=0, microsecond=0)
#     if out == "1M":
#         return ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
#     raise ValueError(out)

# def aggregate(rows: Iterable, to: Interval, *, asc: bool = True):
#     # rows: 1m/1h/1d 원시 캔들. 속성: exi_id, ts_open, open/high/low/close/volume 가정
#     buckets: dict[tuple[int, datetime], dict] = {}
#     for r in rows:
#         key = (r.exchange_instrument_id, _floor(r.ts_open, to))
#         b = buckets.get(key)
#         if b is None:
#             buckets[key] = {
#                 "exi": r.exchange_instrument_id, "ts": key[1],
#                 "high": r.high, "low": r.low,
#                 "vol": (r.volume or Decimal("0")),
#                 "_first_ts": r.ts_open, "_first_open": r.open,
#                 "_last_ts":  r.ts_open, "_last_close": r.close,
#             }
#         else:
#             if r.high > b["high"]: b["high"] = r.high
#             if r.low  < b["low"]:  b["low"]  = r.low
#             if r.volume is not None: b["vol"] += r.volume
#             if r.ts_open < b["_first_ts"]:
#                 b["_first_ts"], b["_first_open"] = r.ts_open, r.open
#             if r.ts_open > b["_last_ts"]:
#                 b["_last_ts"], b["_last_close"] = r.ts_open, r.close

#     out = []
#     for b in buckets.values():
#         out.append(type("Agg", (), {
#             "exchange_instrument_id": b["exi"],
#             "ts_open": b["ts"],
#             "open": b["_first_open"],
#             "high": b["high"],
#             "low": b["low"],
#             "close": b["_last_close"],
#             "volume": b["vol"],
#         }))
#     out.sort(key=lambda x: x.ts_open, reverse=not asc)
#     return out

PRICE_Q = Decimal("1e-16")
VOL_Q   = Decimal("1e-16")


def dec(x: float | Decimal | None) -> Decimal | None:
    if x is None:
        return None
    return Decimal(str(x)).quantize(PRICE_Q, rounding=ROUND_HALF_UP)

def align_utc(ts: datetime, base: CandleBaseInterval, targets: tuple[str]) -> datetime:
    """ts_open을 UTC로 정규화하고 base 경계에 맞는지 검증."""
    ts = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if base == CandleBaseInterval.MIN_1:
        if ts.second or ts.microsecond:
            raise ValidationAppError(f"Invalid {targets[1]} minute-aligned (sec=0, micro=0)", target=targets[1])
    elif base == CandleBaseInterval.HOUR_1:
        if ts.minute or ts.second or ts.microsecond:
            raise ValidationAppError(f"Invalid {targets[1]} hour-aligned (min=0, sec=0, micro=0)", target=targets[1])
    elif base == CandleBaseInterval.DAY_1:
        if ts.hour or ts.minute or ts.second or ts.microsecond:
            raise ValidationAppError(f"Invalid {targets[1]} day-aligned (00:00:00)", target=targets[1])
    else:
        raise ValidationAppError(f"Unsupported base interval: {targets[0]}", target=targets[0])
    return ts

def q(v: Decimal, q_: Decimal) -> Decimal:
    return v.quantize(q_, rounding=ROUND_DOWN)

class Randomizer:
    """seed로 초기화한 RNG를 재사용. 서비스는 Random을 몰라도 됨."""
    def __init__(self, seed: int | None = None):
        self.rng = Random(seed)

    def base_price(self, lo: float = 1_000, hi: float = 50_000) -> Decimal:
        return q(Decimal(str(self.rng.uniform(lo, hi))), PRICE_Q)

    def ohlcv(self, base_open: Decimal) -> dict:
        up   = Decimal(str(self.rng.uniform(1.0, 1.05)))
        down = Decimal(str(self.rng.uniform(0.95, 1.0)))
        high = q(base_open * up, PRICE_Q)
        low  = q(base_open * down, PRICE_Q)
        close= q(Decimal(str(self.rng.uniform(float(low), float(high)))), PRICE_Q)
        vol  = q(Decimal(str(self.rng.uniform(0, 1000))), VOL_Q)
        return {"open": q(base_open, PRICE_Q), "high": high, "low": low, "close": close, "volume": vol}

def batched(iterable, size: int):
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) == size:
            yield batch; batch = []
    if batch: yield batch