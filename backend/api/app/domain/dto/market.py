from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class MarketInstrumentBrief:
    id: int
    exchange_symbol: str
    base_symbol: str
    quote_symbol: str
    exchange_name: str