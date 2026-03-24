import enum


class WsMessageType(str, enum.Enum):
    # client → server
    SUBSCRIBE_LIST = "SUBSCRIBE_LIST"
    UNSUBSCRIBE_LIST = "UNSUBSCRIBE_LIST"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    PMESSAGE = "pmessage"
    MESSAGE = "message"

    INIT = "INIT"

    # server → client
    TICKER = "ticker"
    CANDLE = "candle"
    SNAPSHOT = "SNAPSHOT"

    # error
    ERROR = "error"
