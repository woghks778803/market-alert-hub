import enum

TMP = "tmp"
SNAP = "snap"
STREAM = "stream"
META = "meta"
LOCK = "lock"
CURSOR = "cursor"

CANDLE = "candle"
TICKER = "ticker"
TICKERS = "tickers"

COOLDOWN = "cooldown"
PUBLISH = "publish"
STATE = "state"

SYMBOLS = "symbols"
EXCHANGES = "exchanges"


class BaseQuote(str, enum.Enum):
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    KRW = "KRW"


class ExchangeCode(str, enum.Enum):
    UPBIT = "UPBIT"
    BINANCE = "BINANCE"
    BITHUMB = "BITHUMB"


class OAutheCode(str, enum.Enum):
    KAKAO = "KAKAO"


class MarketSort(str, enum.Enum):
    VOLUME_DESC = "volume_desc"
    CHANGE_DESC = "change_desc"
    CHANGE_ASC = "change_asc"
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"


class OutboxEventType(str, enum.Enum):
    AUTH_EMAIL_VERIFY = "AUTH_EMAIL_VERIFY"
    AUTH_PASSWORD_RESET = "AUTH_PASSWORD_RESET"

    CLEANUP_DELETED_USERS = "CLEANUP_DELETED_USERS"

    SYNC_EXCHANGES = "SYNC_EXCHANGES"
    SYNC_SYMBOLS = "SYNC_SYMBOLS"
    SYNC_TICKERS = "SYNC_TICKERS"

    TRIGGER_ALERTS = "TRIGGER_ALERTS"
    PERSIST_SNAPSHOTS = "PERSIST_SNAPSHOTS"


class DeploymentEnvironment(str, enum.Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGE = "stage"
    PROD = "prod"


class TickerInterval(str, enum.Enum):
    HOUR_24 = "24h"


class CandleInterval(str, enum.Enum):
    SEC_1 = "1s"
    MIN_1 = "1m"
    HOUR_1 = "1h"
    DAY_1 = "1d"


class CandleBaseInterval(str, enum.Enum):
    MIN_1 = "1m"
    HOUR_1 = "1h"
    DAY_1 = "1d"


class CandleOutputInterval(str, enum.Enum):
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"

    @property
    def calc_mapping(self):
        return {
            "1m": {"1m", "5m", "15m"},
            "1h": {"1h", "4h"},
            "1d": {"1d", "1w", "1M"},
        }[self.value]


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class EmailVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class DeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class AssetType(str, enum.Enum):
    CRYPTO = "crypto"
    FIAT = "fiat"
    FX = "fx"
    STOCK = "stock"
    FUTURE = "future"


class AlertScope(str, enum.Enum):
    SINGLE = "single"
    CROSS = "cross"
