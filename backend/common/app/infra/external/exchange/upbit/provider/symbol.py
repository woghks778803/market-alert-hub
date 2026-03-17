from dataclasses import dataclass

from app.domain import MarketDTO, MarketPort
from app.infra.external.exchange.upbit.rest_client import UpbitRestClient


@dataclass
class UpbitSymbol(MarketPort.ExchangeSymbol):
    rest_client: UpbitRestClient

    def list_symbols(self) -> list[MarketDTO.SymbolInfo]:
        rows = self.rest_client.list_markets()  # list[UpbitMarket] 가정

        result: list[MarketDTO.SymbolInfo] = []
        for r in rows:
            try:
                quote, base = r.market.split("-", 1)
            except ValueError:
                continue

            if not quote or not base:
                continue

            result.append(
                MarketDTO.SymbolInfo(
                    symbol=r.market,
                    base=base,
                    quote=quote,
                )
            )
        return result
