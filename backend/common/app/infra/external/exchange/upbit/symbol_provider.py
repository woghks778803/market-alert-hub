from dataclasses import dataclass

from app.domain import MarketDTO, MarketPort
from app.infra.external.exchange.upbit.rest_client import UpbitRestClient

@dataclass
class UpbitSymbolProvider(MarketPort.UpbitSymbolProvider):
    rest_client: UpbitRestClient

    def list_symbols(self) -> list[MarketDTO.SymbolInfo]:
        rows = self.rest_client.list_markets()  # list[UpbitMarket] 가정

        result: list[MarketDTO.SymbolInfo] = []
        for r in rows:
            result.append(
                MarketDTO.SymbolInfo(
                    symbol=r.market,
                    name_kr=r.korean_name,
                    name_en=r.english_name,
                )
            )
        return result
