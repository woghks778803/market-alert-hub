class BinanceError(Exception):
    """Base error for Binance external adapter."""


class BinanceHttpError(BinanceError):
    def __init__(self, status: int, message: str, *, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


class BinanceRateLimitError(BinanceHttpError):
    """429 or rate-limit like responses."""


class BinanceDecodeError(BinanceError):
    """Failed to decode/parse Binance payload."""


class BinanceWsError(BinanceError):
    """WebSocket connection/subscription/runtime errors."""
