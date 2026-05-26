from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.core.constants import (
    CandleBaseInterval
)
from app.core.util.datetime import parse_iso_utc
from app.domain import MarketDTO, MarketPort
from app.infra.external.exchange.upbit.rest_client import UpbitRestClient
from app.infra.external.exchange.upbit.shared.errors import UpbitDecodeError


@dataclass
class UpbitCandle(MarketPort.ExchangeCandle):
    rest_client: UpbitRestClient

    def list_candle(
        self,
        *,
        base: CandleBaseInterval,
        exchange_symbol: str,
        to: datetime,
        count: int,
    ) -> list[MarketDTO.CandleInfo] | None:
        if base == CandleBaseInterval.MIN_1:
            rows = self.rest_client.list_minute_candle(
                unit=1,
                market=exchange_symbol,
                to=to,
                count=count,
            )
        elif base == CandleBaseInterval.HOUR_1:
            rows = self.rest_client.list_minute_candle(
                unit=60,
                market=exchange_symbol,
                to=to,
                count=count,
            )
        elif base == CandleBaseInterval.DAY_1:
            rows = self.rest_client.list_day_candle(
                market=exchange_symbol,
                to=to,
                count=count,
            )
        # 나중에 추가
        # elif base == CandleBaseInterval.WEEK_1:
        #     rows = self.rest_client.list_week_candles(...)
        # elif base == CandleBaseInterval.MONTH_1:
        #     rows = self.rest_client.list_month_candles(...)
        else:
            return None

        result: list[MarketDTO.CandleInfo] = []

        for row in rows:
            try:
                opened_at = parse_iso_utc(row["candle_date_time_utc"])

                result.append(
                    MarketDTO.CandleInfo(
                        opened_at=opened_at,
                        open_price=Decimal(str(row["opening_price"])),
                        high_price=Decimal(str(row["high_price"])),
                        low_price=Decimal(str(row["low_price"])),
                        close_price=Decimal(str(row["trade_price"])),
                        volume=Decimal(str(row["candle_acc_trade_volume"])),
                    )
                )
            except KeyError as e:
                raise UpbitDecodeError(f"Missing candle field: {e}") from e
            except Exception as e:
                raise UpbitDecodeError(f"Failed to parse Upbit candle: {e}") from e

        return result
