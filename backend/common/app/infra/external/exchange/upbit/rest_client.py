from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.infra.external.transport.port.http import SyncHttpTransport
from app.infra.external.transport.impl.httpx import (
    HttpxTransport,
    HttpxTransportConfig,
)
from .shared.errors import UpbitHttpError, UpbitRateLimitError, UpbitDecodeError
from .shared.dto import UpbitMarket

@dataclass(frozen=True)
class UpbitRestClientConfig:
    base_url: str
    timeout_sec: float = 10.0


class UpbitRestClient:
    def __init__(
        self,
        config: UpbitRestClientConfig,
        *,
        transport: SyncHttpTransport | None = None,
    ) -> None:
        if not config.base_url:
            raise RuntimeError("Upbit base_url is required")

        self._config = config
        self._transport = transport or HttpxTransport(
            HttpxTransportConfig(
                base_url=self._config.base_url,
                timeout_sec=self._config.timeout_sec,
            )
        )

    def __enter__(self) -> "UpbitRestClient":
        # transport가 context manager일 수도 있으니 가능하면 진입
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
            raise UpbitRateLimitError(
                resp.status_code, "Upbit rate limited", body=resp.text
            )
        if resp.status_code >= 400:
            raise UpbitHttpError(
                resp.status_code,
                f"Upbit http error: {resp.status_code}",
                body=resp.text,
            )

        try:
            return resp.json()
        except Exception as e:
            raise UpbitDecodeError(f"Failed to decode Upbit response: {e}") from e

    def list_market(self) -> list[UpbitMarket]:
        data = self._get_json("/v1/market/all", params={"isDetails": "false"})
        if not isinstance(data, list):
            raise UpbitDecodeError("Unexpected markets payload shape")

        out: list[UpbitMarket] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            market = item.get("market")
            kname = item.get("korean_name")
            ename = item.get("english_name")
            if market and kname and ename:
                out.append(
                    UpbitMarket(market=market, korean_name=kname, english_name=ename)
                )
        return out

    def list_minute_candle(
        self,
        *,
        unit: int,
        market: str,
        to: datetime,
        count: int,
    ) -> list[dict[str, Any]]:
        data = self._get_json(
            f"/v1/candles/minutes/{unit}",
            params={
                "market": market,
                "to": to.strftime("%Y-%m-%dT%H:%M:%S"),
                "count": count,
            },
        )

        if not isinstance(data, list):
            raise UpbitDecodeError("Unexpected minute candles payload shape")

        return [item for item in data if isinstance(item, dict)]

        return result

    def list_day_candle(
        self,
        *,
        market: str,
        to: datetime,
        count: int,
    ) -> list[dict[str, Any]]:
        data = self._get_json(
            "/v1/candles/days",
            params={
                "market": market,
                "to": to.strftime("%Y-%m-%dT%H:%M:%S"),
                "count": count,
            },
        )

        if not isinstance(data, list):
            raise UpbitDecodeError("Unexpected day candle payload shape")

        return [item for item in data if isinstance(item, dict)]


def get_upbit_rest_client(
    config: UpbitRestClientConfig
) -> UpbitRestClient:
    return UpbitRestClient(config)
