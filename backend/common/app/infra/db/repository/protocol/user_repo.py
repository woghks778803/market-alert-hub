from typing import Protocol
from app.infra.db.model import UserModel
from app.domain import EmailDTO, UserDTO, AuthDTO
from datetime import datetime


class UserRepo(Protocol):
    def add_user_oauth_accounts(
        self, user_oauth_account: UserDTO.UserOAuthAccountCreate
    ) -> UserDTO.UserOAuthAccount: ...
    def add_user(self, user: UserDTO.UserCreate) -> UserDTO.User: ...
    def add_email_verification(
        self, email_verification: UserDTO.EmailVerificationCreate
    ) -> UserDTO.EmailVerification: ...
    def add_password_reset(
        self, password_reset: UserDTO.PasswordResetCreate
    ) -> UserDTO.PasswordReset: ...
    def get_user_by_email_fingerprint(
        self, email_fingerprint: bytes
    ) -> UserDTO.User | None: ...
    def get_by_user_id(self, user_id: int) -> UserDTO.User | None: ...
    def get_password_reset_by_id(
        self, password_reset_id: int
    ) -> UserDTO.PasswordReset | None: ...
    def get_password_reset_by_token_hash(
        self,
        token_hash: bytes,
        consumed_is_null: bool = True,
        expires_after: datetime | None = None,
    ) -> UserDTO.PasswordReset | None: ...
    def get_email_verification_by_id(
        self, email_verification_id: int
    ) -> UserDTO.EmailVerification | None: ...
    def get_email_verification_by_token_hash(
        self, token_hash: bytes
    ) -> UserDTO.EmailVerification | None: ...
    def get_oauth_provider_by_code(
        self, code: str, is_active: bool | None = None
    ) -> UserDTO.OauthProvider | None: ...
    def get_oauth_account_by_filter(
        self,
        oauth_provider_id: int,
        provider_user_id: str,
        unlinked_at_is_null: bool | None = None,
    ) -> UserDTO.UserOAuthAccount | None: ...
    def list_users_filter(
        self, *, status: str | None, role: str | None, limit: int, offset: int
    ) -> list[UserDTO.User]: ...
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
        consumed_at: datetime | None = None,
        sent_is_null: bool | None = None,
        consumed_is_null: bool | None = None,
    ) -> int: ...
    def update_user_last_login_at(
        self, user_id: int, last_login_at: datetime
    ) -> None: ...
    def update_user_email_verified_at(
        self, user_id: int, email_verified_at: datetime
    ) -> None: ...
    def update_user_email(
        self,
        id: int,
        email_fingerprint: bytes | None = None,
        email_ciphertext: bytes | None = None,
        email_nonce: bytes | None = None,
        email_key_version: int | None = None,
    ) -> None: ...
