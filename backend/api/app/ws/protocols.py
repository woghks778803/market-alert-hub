import enum


class WsMessageType(str, enum.Enum):
    # client → server
    SUBSCRIBE_LIST = "SUBSCRIBE_LIST"
    UNSUBSCRIBE_LIST = "UNSUBSCRIBE_LIST"
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"

    PMESSAGE = "pmessage"
    MESSAGE = "message"

    # server → client
    INIT = "init"
    PONG = "pong"
    TICKER = "ticker"
    CANDLE = "candle"
    SNAPSHOT = "snapshot"

    # error
    ERROR = "error"
