from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.core.constants import CandleBaseInterval
from app.core.util.datetime import epoch_to_datetime
from app.domain import MarketDTO, MarketPort
from app.infra.external.exchange.binance.rest_client import BinanceRestClient
from app.infra.external.exchange.binance.shared.errors import BinanceDecodeError


@dataclass
class BinanceCandle(MarketPort.ExchangeCandle):
    rest_client: BinanceRestClient

    def list_candle(
        self,
        *,
        base: CandleBaseInterval,
        exchange_symbol: str,
        to: datetime,
        count: int,
    ) -> list[MarketDTO.CandleInfo] | None:
        rows = self.rest_client.list_kline(
            symbol=exchange_symbol,
            interval=base.value,
            end_time=to,
            limit=count,
        )

        result: list[MarketDTO.CandleInfo] = []

        for row in rows:
            if not isinstance(row, list):
                continue

            try:
                # Binance kline 배열:
                # 0 open time, 1 open, 2 high, 3 low, 4 close, 5 volume, ...
                opened_at = epoch_to_datetime(
                    int(row[0]) / 1000
                )

                result.append(
                    MarketDTO.CandleInfo(
                        opened_at=opened_at,
                        open_price=Decimal(str(row[1])),
                        high_price=Decimal(str(row[2])),
                        low_price=Decimal(str(row[3])),
                        close_price=Decimal(str(row[4])),
                        volume=Decimal(str(row[5])),
                    )
                )
            except (IndexError, TypeError, ValueError) as e:
                raise BinanceDecodeError(f"Failed to parse Binance kline: {e}") from e

        return result