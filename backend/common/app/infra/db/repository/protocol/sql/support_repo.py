from typing import Protocol, Sequence
from app.domain import SupportDTO
from app.core.constants import NoticeCategory, FAQCategory

class SupportRepo(Protocol): 
    def get_notice_by_id(self, id: int, is_active: bool = True) -> SupportDTO.NoticeDetail | None: ...
    def list_notice_by_filter(
        self, 
        category: NoticeCategory | None, 
        is_active: bool = True, 
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SupportDTO.Notice]: ...
    def list_faq_by_filter(
        self, 
        search: str | None,
        category: FAQCategory | None, 
        is_active: bool = True, 
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[SupportDTO.FAQ]: ...
    def update_notice_view_count(
        self,
        id: int
    ) -> int: ...