from dataclasses import dataclass
from decimal import Decimal

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
                    tick_size=(
                        Decimal(r.tick_size)
                        if r.tick_size is not None
                        else None
                    ),
                    price_precision=r.price_precision,
                    qty_precision=r.qty_precision,
                    min_notional=(
                        Decimal(r.min_notional)
                        if r.min_notional is not None
                        else None
                    ),
                )
            )
        return result
