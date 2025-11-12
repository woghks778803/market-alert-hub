import enum
    
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
            "1m": {"1m","5m","15m"},
            "1h": {"1h","4h"},
            "1d": {"1d","1w","1M"},
        }[self.value]

class UserRole(str, enum.Enum):
    USER  = "user"
    ADMIN = "admin"

class OutboxStatus(str, enum.Enum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    
class UserStatus(str, enum.Enum):
    ACTIVE    = "active"
    SUSPENDED = "suspended"
    DELETED   = "deleted"

class AlertStatus(str, enum.Enum):
    ACTIVE   = "active"
    PAUSED   = "paused"
    ARCHIVED = "archived"

class DeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT   = "sent"
    FAILED = "failed"

class AssetType(str, enum.Enum):
    CRYPTO = "crypto"; FIAT = "fiat"; FX = "fx"; STOCK = "stock"; FUTURE = "future"

class AlertType(str, enum.Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    PCT_CHANGE_WINDOW = "pct_change_window"
    CROSS_EXCHANGE_SPREAD = "cross_exchange_spread"
    VOLUME_ABOVE = "volume_above"
    MOVING_AVG_CROSS = "moving_avg_cross"

class AlertScope(str, enum.Enum):
    SINGLE = "single"
    CROSS  = "cross"

class EmailVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"

# 에러 코드 / 메시지
ERROR_INVALID_TOKEN: str = "Invalid token"
ERROR_PERMISSION_DENIED: str = "Permission denied"