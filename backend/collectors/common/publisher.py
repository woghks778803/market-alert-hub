import os
from .redis_client import streams


def publish_tick(exchange: str, symbol: str, price: float):
    payload = {"exchange": exchange, "symbol": symbol, "price": price}
    streams().publish(payload)
