import os, time, random
from ..common.directory import symbols
from ..common.publisher import publish_tick


SYMS = symbols(["BTC/USDT", "ETH/USDT"])


if os.getenv("MOCK_MODE", "true").lower() == "true":
    while True:
        sym = random.choice(SYMS)
        price = round(random.uniform(1000, 100000), 2)
        publish_tick(exchange="UPBIT", symbol=sym, price=price)
        time.sleep(1)
