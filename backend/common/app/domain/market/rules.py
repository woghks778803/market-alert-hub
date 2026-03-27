from typing import Literal
from random import Random
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from app.core.util.datetime import utcnow
from app.core.constants import CandleBaseInterval, CandleOutputInterval
from app.domain.shared.errors import ValidationAppError
import app.domain.market.dto as MarketDTO

Interval = Literal["1m", "5m", "15m", "1h", "4h", "1d", "1w", "1M"]


def compose_candle_snapshot_data(
    market_simples: list[MarketDTO.MarketSimple],
    snapshots: list[MarketDTO.PriceSnapshotCreate],
) -> list:
    snapshot_map = {s.exchange_instrument_id: s for s in snapshots}
    merged = [
        {
            "ts_open": int(s.ts_open.timestamp() * 1000),
            "open": str(s.open),
            "close": str(s.close),
            "high": str(s.high),
            "low": str(s.low),
            "volume": str(s.volume),
            "exchange_code": m.exchange_code,
            "exchange_symbol": m.exchange_symbol,
        }
        for m in market_simples
        if (s := snapshot_map.get(m.id)) is not None
    ]
    return merged


def compose_ticker_snapshot_data(
    market_simples: list[MarketDTO.MarketSimple],
    snapshots: list[MarketDTO.ExchangeInstrumentTickerCreate],
) -> list:
    snapshot_map = {s.exchange_instrument_id: s for s in snapshots}

    merged = [
        {
            "ts": int(utcnow().timestamp() * 1000),
            "price": str(s.close_price),
            "open": str(s.open_price),
            "high": str(s.high_24h),
            "low": str(s.low_24h),
            "volume": str(s.volume_24h),
            "price_change": str(s.price_change_24h),
            "change_rate": str(s.price_change_rate_24h),
            "normalized_price": str(s.normalized_price),
            "normalized_volume": str(s.normalized_volume),
            "exchange_code": m.exchange_code,
            "exchange_symbol": m.exchange_symbol,
        }
        for m in market_simples
        if (s := snapshot_map.get(m.id)) is not None
    ]

    return merged


def parse_market_symbol(symbol: str) -> MarketDTO.ParsedMarketSymbol | None:
    # "KRW-BTC" 형태 파싱 (업비트 스펙 기반)
    try:
        quote, base = symbol.split("-", 1)
    except ValueError:
        return None
    if not quote or not base:
        return None
    return MarketDTO.ParsedMarketSymbol(quote=quote, base=base)


def choose_source_base(output):
    if output in CandleOutputInterval.MIN_1.calc_mapping:
        return CandleBaseInterval.MIN_1
    if output in CandleOutputInterval.HOUR_1.calc_mapping:
        return CandleBaseInterval.HOUR_1
    if output in CandleOutputInterval.DAY_1.calc_mapping:
        return CandleBaseInterval.DAY_1
    raise ValidationAppError(f"Unsupported output : {output}", target="output")


def same_granularity(base: CandleBaseInterval, output: CandleOutputInterval) -> bool:
    # base와 output이 같은 크기면 그대로 반환
    return (
        (base == CandleBaseInterval.MIN_1 and output == CandleOutputInterval.MIN_1)
        or (base == CandleBaseInterval.HOUR_1 and output == CandleOutputInterval.HOUR_1)
        or (base == CandleBaseInterval.DAY_1 and output == CandleOutputInterval.DAY_1)
    )


def interval_seconds(label: str) -> int:
    # '1m','5m','15m','1h','4h','1d','1w','1M' -> 초
    if label.endswith("m"):
        return int(label[:-1]) * 60
    if label.endswith("h"):
        return int(label[:-1]) * 60 * 60
    if label.endswith("d"):
        return int(label[:-1]) * 60 * 60 * 24
    if label.endswith("w"):
        return int(label[:-1]) * 7 * 60 * 60 * 24
    if label.endswith("M"):
        return 30 * 60 * 60 * 24  # rough; limit 추정용
    raise ValueError(label)


def calc_source_limit(
    base: CandleBaseInterval,
    output: CandleOutputInterval,
    limit: int | None,
) -> int | None:
    """output을 만들기 위해 base에서 얼마나 읽을지 계산."""
    if limit is None:
        return None
    if same_granularity(base, output):
        return limit

    # output이 base의 배수가 아니면(예: base=1h, output=15m) 금지
    base_s = interval_seconds(base.value)
    out_s = interval_seconds(output.value)

    if out_s < base_s or (out_s % base_s) != 0:
        # 지원 조합: 1m→(5m/15m/1h/4h/1d), 1h→(4h/1d), 1d→(1w/1M)
        raise ValidationAppError(
            f"Unsupported rollup combination: base={base.value}, output={output.value}",
            target="base, output",
        )
    factor = out_s // base_s

    # 버킷 정렬 오차 대비 + (factor-1) 여유 > 나중에 이상이 있다면 고려
    return limit * int(factor)


""" output에 따라 롤업 데이터 초기화 """


def _floor(ts: datetime, out: Interval) -> datetime:
    ts = ts.astimezone(timezone.utc).replace(tzinfo=timezone.utc)
    if out.endswith("m"):
        m = int(out[:-1])
        return ts.replace(second=0, microsecond=0, minute=(ts.minute // m) * m)
    if out.endswith("h"):
        h = int(out[:-1])
        return ts.replace(minute=0, second=0, microsecond=0, hour=(ts.hour // h) * h)
    if out == "1d":
        return ts.replace(hour=0, minute=0, second=0, microsecond=0)
    if out == "1w":
        d = (ts.isoweekday() - 1) % 7
        base = ts - timedelta(days=d)
        return base.replace(hour=0, minute=0, second=0, microsecond=0)
    if out == "1M":
        return ts.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(out)


def aggregate(
    rows: list[MarketDTO.CandleBase], to: Interval, *, asc: bool = True
) -> list[MarketDTO.CandleBase]:
    # rows: 1m/1h/1d 원시 캔들. 속성: exi_id, ts_open, open/high/low/close/volume 가정
    buckets: dict[tuple[int, datetime], dict] = {}
    for r in rows:
        key = (r.exchange_instrument_id, _floor(r.ts_open, to))
        b = buckets.get(key)
        if b is None:
            buckets[key] = {
                "exi": r.exchange_instrument_id,
                "ts": key[1],
                "high": r.high,
                "low": r.low,
                "vol": (r.volume or Decimal("0")),
                "_first_ts": r.ts_open,
                "_first_open": r.open,
                "_last_ts": r.ts_open,
                "_last_close": r.close,
            }
        else:
            if r.high > b["high"]:
                b["high"] = r.high
            if r.low < b["low"]:
                b["low"] = r.low
            if r.volume is not None:
                b["vol"] += r.volume
            if r.ts_open < b["_first_ts"]:
                b["_first_ts"], b["_first_open"] = r.ts_open, r.open
            if r.ts_open > b["_last_ts"]:
                b["_last_ts"], b["_last_close"] = r.ts_open, r.close

    out = []
    for b in buckets.values():
        out.append(
            MarketDTO.CandleBase(
                exchange_instrument_id=b["exi"],
                ts_open=b["ts"],
                open=float(b["_first_open"]),
                high=float(b["high"]),
                low=float(b["low"]),
                close=float(b["_last_close"]),
                volume=float(b["vol"]),
            )
        )
    out.sort(key=lambda x: x.ts_open, reverse=not asc)
    return out


PRICE_Q = Decimal("1e-16")
VOL_Q = Decimal("1e-16")


def dec(x: float | Decimal) -> Decimal:
    return Decimal(str(x)).quantize(PRICE_Q, rounding=ROUND_HALF_UP)


def align_utc(
    ts: datetime, base: CandleBaseInterval, targets: tuple[str, ...]
) -> datetime:
    """ts_open을 UTC로 정규화하고 base 경계에 맞는지 검증."""
    ts = ts.astimezone(timezone.utc) if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    if base == CandleBaseInterval.MIN_1:
        if ts.second or ts.microsecond:
            raise ValidationAppError(
                f"Invalid {targets[1]} minute-aligned (sec=0, micro=0)",
                target=targets[1],
            )
    elif base == CandleBaseInterval.HOUR_1:
        if ts.minute or ts.second or ts.microsecond:
            raise ValidationAppError(
                f"Invalid {targets[1]} hour-aligned (min=0, sec=0, micro=0)",
                target=targets[1],
            )
    elif base == CandleBaseInterval.DAY_1:
        if ts.hour or ts.minute or ts.second or ts.microsecond:
            raise ValidationAppError(
                f"Invalid {targets[1]} day-aligned (00:00:00)", target=targets[1]
            )
    else:
        raise ValidationAppError(
            f"Unsupported base interval: {targets[0]}", target=targets[0]
        )
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
        up = Decimal(str(self.rng.uniform(1.0, 1.05)))
        down = Decimal(str(self.rng.uniform(0.95, 1.0)))
        high = q(base_open * up, PRICE_Q)
        low = q(base_open * down, PRICE_Q)
        close = q(Decimal(str(self.rng.uniform(float(low), float(high)))), PRICE_Q)
        vol = q(Decimal(str(self.rng.uniform(0, 1000))), VOL_Q)
        return {
            "open": q(base_open, PRICE_Q),
            "high": high,
            "low": low,
            "close": close,
            "volume": vol,
        }


def batched(iterable, size: int):
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch
