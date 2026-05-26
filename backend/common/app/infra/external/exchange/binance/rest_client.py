from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.core.util.datetime import datetime_to_epoch_ms
from app.infra.external.transport.port.http import SyncHttpTransport
from app.infra.external.transport.impl.httpx import (
    HttpxTransport,
    HttpxTransportConfig,
)
from .shared.errors import (
    BinanceDecodeError,
    BinanceHttpError,
    BinanceRateLimitError,
)
from .shared.dto import BinanceMarket


@dataclass(frozen=True)
class BinanceRestClientConfig:
    base_url: str
    timeout_sec: float = 10.0


class BinanceRestClient:
    def __init__(
        self,
        config: BinanceRestClientConfig,
        *,
        transport: SyncHttpTransport | None = None,
    ) -> None:
        if not config.base_url:
            raise RuntimeError("Binance base_url is required")

        self._config = config
        self._transport = transport or HttpxTransport(
            HttpxTransportConfig(
                base_url=self._config.base_url,
                timeout_sec=self._config.timeout_sec,
            )
        )

    def __enter__(self) -> "BinanceRestClient":
        enter = getattr(self._transport, "__enter__", None)
        if callable(enter):
            enter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._transport.close()

    def _get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        resp = self._transport.get(path, params=params)

        if resp.status_code == 429:
            raise BinanceRateLimitError(
                resp.status_code, "Binance rate limited", body=resp.text
            )
        if resp.status_code >= 400:
            raise BinanceHttpError(
                resp.status_code,
                f"Binance http error: {resp.status_code}",
                body=resp.text,
            )

        try:
            return resp.json()
        except Exception as e:
            raise BinanceDecodeError(f"Failed to decode Binance response: {e}") from e

    def _get_price_precision(self, tick_size: str | None) -> int | None:
        if not tick_size:
            return None

        normalized = tick_size.rstrip("0")

        if "." not in normalized:
            return 0

        return len(normalized.split(".", 1)[1])

    def list_market(self) -> list[BinanceMarket]:
        data = self._get_json("/api/v3/exchangeInfo")
        symbols = data.get("symbols") if isinstance(data, dict) else None
        if not isinstance(symbols, list):
            raise BinanceDecodeError("Unexpected exchangeInfo payload shape")

        out: list[BinanceMarket] = []
        for item in symbols:
            if not isinstance(item, dict):
                continue
            sym = item.get("symbol")
            base = item.get("baseAsset")
            quote = item.get("quoteAsset")
            status = item.get("status")
            raw_price_precision = item.get("pricePrecision")
            raw_qty_precision = item.get("quantityPrecision")

            if not (
                isinstance(sym, str)
                and isinstance(base, str)
                and isinstance(quote, str)
                and status == "TRADING"
            ):
                continue

            price_precision: int | None = (
                raw_price_precision if isinstance(raw_price_precision, int) else None
            )
            qty_precision: int | None = (
                raw_qty_precision if isinstance(raw_qty_precision, int) else None
            )

            tick_size: str | None = None
            min_notional: str | None = None

            filters = item.get("filters", [])
            if isinstance(filters, list):
                for f in filters:
                    if not isinstance(f, dict):
                        continue

                    filter_type = f.get("filterType")

                    if filter_type == "PRICE_FILTER":
                        raw_tick_size = f.get("tickSize")
                        if isinstance(raw_tick_size, str):
                            tick_size = raw_tick_size

                    elif filter_type in ("MIN_NOTIONAL", "NOTIONAL"):
                        raw_min_notional = f.get("minNotional")
                        if isinstance(raw_min_notional, str):
                            min_notional = raw_min_notional

                    break

            price_precision = self._get_price_precision(tick_size)
        
            out.append(
                BinanceMarket(
                    symbol=sym,
                    base_asset=base,
                    quote_asset=quote,
                    tick_size=tick_size,
                    price_precision=price_precision,
                    qty_precision=qty_precision,
                    min_notional=min_notional,
                )
            )
        return out

    def list_kline(
        self,
        *,
        symbol: str,
        interval: str,
        end_time: datetime,
        limit: int,
    ) -> Any:
        data = self._get_json(
            "/api/v3/klines",
            params={
                "symbol": symbol,
                "interval": interval,
                "endTime": datetime_to_epoch_ms(end_time),
                "limit": limit,
            },
        )

        if not isinstance(data, list):
            raise BinanceDecodeError("Unexpected kline payload shape")

        return data


def get_binance_rest_client(
    config: BinanceRestClientConfig,
) -> BinanceRestClient:
    return BinanceRestClient(config)
