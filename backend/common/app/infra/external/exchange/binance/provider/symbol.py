from dataclasses import dataclass

from app.domain import MarketDTO, MarketPort
from app.infra.external.exchange.binance.rest_client import BinanceRestClient


@dataclass
class BinanceSymbol(MarketPort.ExchangeSymbol):
    rest_client: BinanceRestClient

    def list_symbols(self) -> list[MarketDTO.SymbolInfo]:
        rows = self.rest_client.list_markets()

        result: list[MarketDTO.SymbolInfo] = []
        for r in rows:
            result.append(
                MarketDTO.SymbolInfo(
                    symbol=r.symbol,
                    base=r.base_asset,  # Binance는 별도 한글명이 없으므로 기초/호가 자산을 표기
                    quote=r.quote_asset,
                    tick_size=r.tick_size,
                    price_precision=r.price_precision,
                    qty_precision=r.qty_precision,
                    min_notional=r.min_notional,
                )
            )
        return result
