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
    SNAPSHOT = "snapshot"

    # error
    ERROR = "error"


class WsChannelType(str, enum.Enum):
    TICKER_LIST = "ticker_list"
    CANDLE_LIST = "candle_list"
    TICKER = "ticker"
    CANDLE = "candle"