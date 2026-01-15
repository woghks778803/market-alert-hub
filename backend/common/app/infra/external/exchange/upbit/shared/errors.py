class UpbitError(Exception):
    """Base error for Upbit external adapter."""


class UpbitHttpError(UpbitError):
    def __init__(self, status: int, message: str, *, body: str | None = None):
        super().__init__(message)
        self.status = status
        self.body = body


class UpbitRateLimitError(UpbitHttpError):
    """429 or rate-limit like responses."""


class UpbitDecodeError(UpbitError):
    """Failed to decode/parse Upbit payload."""


class UpbitWsError(UpbitError):
    """WebSocket connection/subscription/runtime errors."""
