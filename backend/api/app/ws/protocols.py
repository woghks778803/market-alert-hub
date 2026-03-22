import enum


class WsMessageType(str, enum.Enum):
    # client → server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # server → client
    TICKER = "ticker"
    CANDLE = "candle"

    # error
    ERROR = "error"
