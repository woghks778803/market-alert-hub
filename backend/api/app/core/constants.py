import enum

class UserRole(str, enum.Enum):
    USER  = "user"
    ADMIN = "admin"

class UserStatus(str, enum.Enum):
    ACTIVE    = "active"
    SUSPENDED = "suspended"
    DELETED   = "deleted"

class AlertStatus(str, enum.Enum):
    ACTIVE   = "active"
    PAUSED   = "paused"
    ARCHIVED = "archived"

class AssetType(str, enum.Enum):
    CRYPTO = "crypto"; FX = "fx"; STOCK = "stock"; FUTURE = "future"

class ActiveStatus(str, enum.Enum):
    ACTIVE = "active"; INACTIVE = "inactive"

class DeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT   = "sent"
    FAILED = "failed"

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

# 에러 코드 / 메시지
ERROR_INVALID_TOKEN: str = "Invalid token"
ERROR_PERMISSION_DENIED: str = "Permission denied"