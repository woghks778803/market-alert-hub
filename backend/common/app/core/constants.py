import enum

"""
공통 상수 정의
Outbox / 내부 이벤트 - 대문자
Exchange / Symbol - 대문자 유지
외부 통신 - 소문자
"""

TMP = "tmp"
SNAP = "snap"
STREAM = "stream"
PUBLISH = "publish"
META = "meta"
LOCK = "lock"
CURSOR = "cursor"
INDEX = "index"

PRICE = "price"
INDICATOR = "indicator"

CANDLE = "candle"
TICKER = "ticker"
TICKERS = "tickers"

BUCKET= "bucket"
COOLDOWN = "cooldown"
STATE = "state"
SYSTEM = "system"

SYMBOLS = "symbols"
EXCHANGES = "exchanges"
ALERTS = "alerts"

class ThrottleTimeframe(str, enum.Enum):
    MIN_5 = "5m"
    MIN_10 = "10m"
    MIN_30 = "30m"
    HOUR_1 = "1h"
    HOUR_3 = "3h"
    HOUR_6 = "6h"
    HOUR_12 = "12h"
    DAY_1 = "1d"

# 거래소 표준 대문자 유지
class BaseQuote(str, enum.Enum):
    USDT = "USDT"
    BTC = "BTC"
    ETH = "ETH"
    KRW = "KRW"

class ExchangeCode(str, enum.Enum):
    UPBIT = "UPBIT"
    BINANCE = "BINANCE"
    BITHUMB = "BITHUMB"

class ChannelCode(str, enum.Enum):
    FCM = "FCM"
    TELEGRAM = "TELEGRAM"
    DISCORD = "DISCORD"

class TranslationCode(str, enum.Enum):
    GOOGLE = "GOOGLE"

class OAuthCode(str, enum.Enum):
    KAKAO = "KAKAO"

class OAuthResultType(str, enum.Enum):
    TERMS_REQUIRED = "terms_required"
    ERROR = "error"
    SUCCESS = "success"

class NewsPostsort(str, enum.Enum):
    RECENT_UPDATED = "recent_updated"

class MarketSort(str, enum.Enum):
    VOLUME_DESC = "volume_desc"
    CHANGE_DESC = "change_desc"
    CHANGE_ASC = "change_asc"
    PRICE_DESC = "price_desc"
    PRICE_ASC = "price_asc"

class AlertSort(str, enum.Enum):
    RECENT_UPDATED = "recent_updated"   
    RECENT_CREATED = "recent_created"  
    MARKET_ASC = "market_asc"          
    STATUS = "status"    

class LanguageCode(str, enum.Enum):
    KO="ko" # Korean
    EN="en" # English
    JA="ja" # Japanese
    ZH="zh" # Chinese
    UNKNOWN="unknown"

class AlertFormType(str, enum.Enum):
    THRESHOLD = "threshold"          # 기준값 1개: price >= threshold, RSI > 70
    RANGE = "range"                  # 범위 입력: 30 <= RSI <= 70
    PERCENT = "percent"              # 퍼센트 입력: price change >= 5%
    PATTERN = "pattern"
    CROSS = "cross"
    # CROSS_VALUE = "cross_value"      # 값 기준 돌파: RSI crosses 70
    # CROSS_LINE = "cross_line"        # 선 교차: MA short crosses MA long, MACD crosses signal
    BAND = "band"                    # 밴드 기준: Bollinger upper/lower/middle
    COMPARE = "compare"              # A/B 비교: volume > volume_ma

class OutboxEventType(str, enum.Enum):
    AUTH_EMAIL_VERIFY = "AUTH_EMAIL_VERIFY"
    AUTH_PASSWORD_RESET = "AUTH_PASSWORD_RESET"

    CLEANUP_DELETED_USERS = "CLEANUP_DELETED_USERS"

    FETCH_NEWS_FEED = "FETCH_NEWS_FEED"
    TRANSLATE_NEWS_ITEMS = "TRANSLATE_NEWS_ITEMS"

    SYNC_EXCHANGES = "SYNC_EXCHANGES"
    SYNC_SYMBOLS = "SYNC_SYMBOLS"
    SYNC_TICKERS = "SYNC_TICKERS"
    SYNC_ALERTS = "SYNC_ALERTS"

    DISPATCH_ALERT_EVENTS = "DISPATCH_ALERT_EVENTS"
    PERSIST_SNAPSHOTS = "PERSIST_SNAPSHOTS"

class StreamType(str, enum.Enum):
    PERSIST_ALERT_EVENTS = "PERSIST_ALERT_EVENTS"

class CooldownType(str, enum.Enum):
    ALERT_PRICE = "ALERT_PRICE"
    EMAIL_VERIFY_RESEND = "EMAIL_VERIFY_RESEND"
    NOTICE_VIEW = "NOTICE_VIEW"
    NOTICE_VIEW_RATE = "NOTICE_VIEW_RATE"

class PlatformType(str, enum.Enum):
    ANDROID = "android"
    IOS = "ios"

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


# TODO: CandleBaseInterval과 CandleOutputInterval는 차트용 타임프레임으로 추후 변경 필요. 현재는 1m, 1h, 1d만 지원하지만, 향후 5m, 15m, 4h 등 추가될 수 있음
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
    SENDING = "sending" # processing
    SENT = "sent" # done
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


class AlertEventStatus(str, enum.Enum):
    PENDING = "pending"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    SKIPPED = "skipped"


class AlertDeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class NewsItemStatus(str, enum.Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    DELETED = "deleted"


class NewsItemTranslationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class AssetType(str, enum.Enum):
    CRYPTO = "crypto"
    FIAT = "fiat"
    FX = "fx"
    STOCK = "stock"
    FUTURE = "future"

class IndicatorType(str, enum.Enum):
    PRICE = "price"
    VOLUME = "volume"
    CHANGE_RATE = "change_rate"
    RSI = "rsi"
    MACD = "macd"
    MA = "ma"
    EMA = "ema"
    ICHIMOKU = "ichimoku"
    ENVELOPE = "envelope"
    BOLLINGER = "bollinger"

class DirectionType(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    BOTH = "both"

class ConditionType(str, enum.Enum):
    SINGLE = "single"
    CROSS = "cross"

class NoticeCategory(str, enum.Enum):
    UPDATE = "update"
    MAINTENANCE = "maintenance"
    NOTICE = "notice"


class FAQCategory(str, enum.Enum):
    GENERAL = "general"
    ACCOUNT = "account"
    PAYMENT = "payment"
    NOTIFICATION = "notification"


THROTTLE_SECONDS = {
    ThrottleTimeframe.MIN_5: 300,
    ThrottleTimeframe.MIN_10: 600,
    ThrottleTimeframe.MIN_30: 1800,
    ThrottleTimeframe.HOUR_1: 3600,
    ThrottleTimeframe.HOUR_3: 10800,
    ThrottleTimeframe.HOUR_6: 21600,
    ThrottleTimeframe.HOUR_12: 43200,
    ThrottleTimeframe.DAY_1: 86400,
}

