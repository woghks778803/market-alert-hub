from typing import Protocol, Iterable
from app.infra.db.model import UserModel, EmailVerificationModel
from app.core.constants import EmailVerificationStatus
from app.domain import EmailDTO
from datetime import datetime 


class UserRepo(Protocol):

    def add_user(self, user: UserModel) -> UserModel: ...
    def add_email_verification(self, email_verification: EmailVerificationModel) -> EmailVerificationModel: ...
    def get_user_by_email_fingerprint(self, email_fingerprint: bytes) -> UserModel | None: ...
    def get_by_user_id(self, user_id: int) -> UserModel | None: ...
    def get_email_verification_by_id(self, email_verification_id: int) -> EmailVerificationModel | None: ...
    def get_email_verification_by_token_hash(self, token_hash: bytes) -> EmailVerificationModel | None: ...
    def list_users_filter(self, *, status: str | None, role: str | None, limit: int, offset: int) -> list[UserModel]: ...
    def update_email_verifications_status_by_user_id(
        self,
        user_id: int,
        *,
        from_statuses: Iterable[EmailVerificationStatus],
        to_status: EmailVerificationStatus,
        set_expires_at: datetime,
        set_expires_at_to_now: bool = True,
        only_not_expired: bool = True,
    ) -> int: ...
    def update_email_verification_by_filter(
        self,
        filters: EmailDTO.EmailVerificationFilter,
        updates: EmailDTO.EmailVerificationUpdate,
    ) -> int: ...