from typing import Protocol


class Cooldown(Protocol):
    def acquire_email_verify_resend(self, user_id: int, ttl_sec: int) -> bool:
        raise NotImplementedError

    def remain_email_verify_resend(self, user_id: int) -> int:
        raise NotImplementedError
    
    def acquire_notice_view(self, key: str, ttl_sec: int) -> bool:
        raise NotImplementedError

    def acquire_notice_view_rate(self, client_ip: str, ttl_sec: int) -> bool:
        raise NotImplementedError

class AsyncCooldown(Protocol):
    async def acquire_alert_price(self, alert_id: int, ttl_sec: int) -> bool:
        raise NotImplementedError

    async def remain_alert_price(self, alert_id: int) -> int:
        raise NotImplementedError
