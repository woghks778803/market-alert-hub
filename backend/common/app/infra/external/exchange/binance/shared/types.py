from dataclasses import dataclass
from typing import Any, Literal


# ---------- REST ----------
@dataclass(frozen=True)
class BinanceMarket:
    symbol: str
    base_asset: str
    quote_asset: str

    tick_size: str | None
    price_precision: int | None
    qty_precision: int | None
    min_notional: str | None

# ---------- WS ----------

BinanceWsChannel = Literal["trade"]


@dataclass(frozen=True)
class BinanceWsSubscribe:
    """
    Binance는 SUBSCRIBE 메시지로 여러 스트림을 한 번에 등록한다.
    streams 예: ["btcusdt@trade", "ethusdt@trade"]
    """

    streams: list[str]

    def to_payload(self) -> dict[str, Any]:
        return {
            "method": "SUBSCRIBE",
            "params": self.streams,
            "id": 1,
        }
