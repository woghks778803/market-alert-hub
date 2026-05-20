from typing import Callable, Sequence, Dict, Any

from app.core.constants import NoticeCategory, FAQCategory
from app.core import dto as CoreDTO
from app.domain.shared.uow import UnitOfWork
from app.domain import (
    SupportDTO,
    ThrottlePort,
)
from app.domain.shared.errors import (
    NotFoundError,
    RateLimitError
)

class SupportService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        cooldown: ThrottlePort.Cooldown,
        config: CoreDTO.ServiceConfigBag,
    ) -> None: 
        self._uow_factory = uow_factory
        self._cooldown = cooldown
        self._config = config

    def get_notice_by_id(self, id: int, user_id: int | None, client_ip: str | None, cookie_id: str) -> SupportDTO.NoticeDetail:
        with self._uow_factory() as uow:
            row = uow.supports.get_notice_by_id(id)

            if row is None:
                raise NotFoundError(
                    "Notice not found", target="notice"
                )
            
            if client_ip is None and user_id is None:
                return row

            cooldown_sec = self._config.notice_view_cooldown_sec
            ip_rate_sec = self._config.ip_rate_cooldown_sec
            identifier = (
                f"user:{user_id}"
                if user_id
                else f"guest:{cookie_id}"
            )
            key = f"{id}:{identifier}"
            ok_view = self._cooldown.acquire_notice_view(key, cooldown_sec)

            ok_rate = True
            if user_id is None:
                if client_ip is None:
                    return row # 타입 체커가 이전 분기까지 추적해서 narrowing 하지 못해서 타입 체커용 분기를 하나 더 넣음 
                ok_rate = self._cooldown.acquire_notice_view_rate(client_ip, ip_rate_sec)

            # 사용자 조회 체크, ip 요청 체크
            if ok_view and ok_rate: 
                uow.supports.update_notice_view_count(id)

            uow.commit()
            return row
            
    def list_notice_by_filter(
        self,
        category: NoticeCategory | None, limit: int, offset: int
    ) -> Sequence[SupportDTO.Notice]:
        
        with self._uow_factory() as uow:
            return uow.supports.list_notice_by_filter(category=category, limit=limit, offset=offset)

    def list_faq_by_filter(
        self,
        search: str | None, category: FAQCategory | None, limit: int, offset: int
    ) -> Sequence[SupportDTO.FAQ]:

        with self._uow_factory() as uow:
            return uow.supports.list_faq_by_filter(search=search, category=category, limit=limit, offset=offset)
