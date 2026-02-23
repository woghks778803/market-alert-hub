from typing import Protocol, Iterable
from app.infra.db.model import PasswordResetModel, UserModel, EmailVerificationModel
from app.core.constants import EmailVerificationStatus
from app.domain import EmailDTO, UserDTO
from datetime import datetime


class UserRepo(Protocol):

    def add_user(self, user: UserDTO.UserCreate) -> UserDTO.User: ...
    def add_email_verification(
        self, email_verification: UserDTO.EmailVerificationCreate
    ) -> UserDTO.EmailVerification: ...
    def add_password_reset(
        self, password_reset: UserDTO.PasswordResetCreate
    ) -> UserDTO.PasswordReset: ...
    def get_user_by_email_fingerprint(
        self, email_fingerprint: bytes
    ) -> UserModel | None: ...
    def get_by_user_id(self, user_id: int) -> UserModel | None: ...
    def get_password_reset_by_id(
        self, password_reset_id: int
    ) -> UserDTO.PasswordReset | None: ...
    def get_email_verification_by_id(
        self, email_verification_id: int
    ) -> EmailVerificationModel | None: ...
    def get_email_verification_by_token_hash(
        self, token_hash: bytes
    ) -> EmailVerificationModel | None: ...
    def list_users_filter(
        self, *, status: str | None, role: str | None, limit: int, offset: int
    ) -> list[UserModel]: ...
    def update_email_verification_by_filter(
        self,
        filters: EmailDTO.EmailVerificationFilter,
        updates: EmailDTO.EmailVerificationUpdate,
    ) -> int: ...
    def update_password_reset_by_filter(
        self,
        *,
        id: int | None = None,
        expires_after: datetime | None = None,
        sent_at: datetime | None = None,
        sent_is_null: bool = True,
        consumed_is_null: bool = True,
    ) -> int: ...
