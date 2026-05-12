from typing import Sequence
from datetime import datetime
from sqlalchemy import select, update, delete, bindparam, desc, and_, func
from sqlalchemy.orm import Session as DbSession
from app.core.constants import UserStatus
from app.domain import EmailDTO, UserDTO
from app.domain.shared.errors import ValidationAppError
from app.infra.db.model import (
    PasswordResetModel,
    UserModel,
    EmailVerificationModel,
    OauthProviderModel,
    UserOauthAccountModel,
)
from app.infra.db.utils import to_db_value
from app.infra.db.repository.protocol.sql.user_repo import UserRepo


class SqlUserRepo(UserRepo):

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add_user_oauth_account(
        self, user_oauth_account: UserDTO.UserOAuthAccountCreate
    ) -> UserDTO.UserOAuthAccount:
        user_oauth_account = UserOauthAccountModel.from_create_dto(user_oauth_account)
        self._db.add(user_oauth_account)
        self._db.flush()
        return user_oauth_account.to_dto()

    def add_user(self, user: UserDTO.UserCreate) -> UserDTO.User:
        user = UserModel.from_create_dto(user)
        self._db.add(user)
        self._db.flush()
        return user.to_dto()

    def add_email_verification(
        self, email_verification: UserDTO.EmailVerificationCreate
    ) -> UserDTO.EmailVerification:
        email_verification = EmailVerificationModel.from_create_dto(email_verification)
        self._db.add(email_verification)
        self._db.flush()
        return email_verification.to_dto()

    def add_password_reset(
        self, password_reset: UserDTO.PasswordResetCreate
    ) -> UserDTO.PasswordReset:
        password_reset = PasswordResetModel.from_create_dto(password_reset)
        self._db.add(password_reset)
        self._db.flush()
        return password_reset.to_dto()

    def get_user_by_email_fingerprint(
        self, email_fingerprint: bytes
    ) -> UserDTO.User | None:
        stmt = select(UserModel).where(UserModel.email_fingerprint == email_fingerprint)
        result = self._db.execute(stmt).scalar_one_or_none()
        return result.to_dto() if result is not None else None

    def get_with_provider_by_user_id(
        self, user_id: int, deleted_is_null: bool = True
    ) -> UserDTO.UserPublicInfo | None:
        stmt = (
            select(
                UserModel.id,
                UserModel.nickname,
                UserModel.email_ciphertext,
                UserModel.email_nonce,
                UserModel.created_at,
                UserModel.last_login_at,
                UserModel.is_marketing,
                UserModel.is_quiet_hours,
                func.coalesce(OauthProviderModel.code, 'email').label('code'),
                func.coalesce(OauthProviderModel.display_name, '이메일').label('display_name')
            )
            .outerjoin(UserOauthAccountModel, UserOauthAccountModel.user_id == UserModel.id)
            .outerjoin(OauthProviderModel, OauthProviderModel.id == UserOauthAccountModel.oauth_providers_id)
            .where(UserModel.id == user_id)
        )

        if deleted_is_null:
            stmt = stmt.where(UserModel.deleted_at.is_(None))

        row = self._db.execute(stmt).one_or_none()
        return UserDTO.UserPublicInfo(
            id=row.id,
            nickname=row.nickname,
            email_ciphertext=row.email_ciphertext,
            email_nonce=row.email_nonce,
            created_at=row.created_at,
            last_login_at=row.last_login_at,
            is_marketing=row.is_marketing,
            is_quiet_hours=row.is_quiet_hours,
            provider_code=row.code,
            provider_display_name=row.display_name,
        ) if row else None

    def get_by_user_id(
        self, user_id: int, deleted_is_null: bool = True
    ) -> UserDTO.User | None:
        stmt = select(UserModel).where(and_(UserModel.id == user_id))

        if deleted_is_null:
            stmt = stmt.where(UserModel.deleted_at.is_(None))

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_password_reset_by_id(
        self, password_reset_id: int
    ) -> UserDTO.PasswordReset | None:
        stmt = select(PasswordResetModel).where(
            PasswordResetModel.id == password_reset_id
        )
        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_password_reset_by_token_hash(
        self,
        token_hash: bytes,
        consumed_is_null: bool = True,
        expires_after: datetime | None = None,
    ) -> UserDTO.PasswordReset | None:
        stmt = select(PasswordResetModel).where(
            PasswordResetModel.token_hash == token_hash
        )

        if consumed_is_null:
            stmt = stmt.where(PasswordResetModel.consumed_at.is_(None))
        if expires_after is not None:
            stmt = stmt.where(PasswordResetModel.expires_at > expires_after)

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_email_verification_by_id(
        self, email_verification_id: int
    ) -> UserDTO.EmailVerification | None:
        stmt = select(EmailVerificationModel).where(
            EmailVerificationModel.id == email_verification_id
        )
        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_email_verification_by_token_hash(
        self, token_hash: bytes
    ) -> UserDTO.EmailVerification | None:
        stmt = select(EmailVerificationModel).where(
            EmailVerificationModel.token_hash == token_hash
        )
        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_oauth_provider_by_code(
        self, code: str, is_active: bool | None = None
    ) -> UserDTO.OauthProvider | None:
        stmt = select(OauthProviderModel).where(OauthProviderModel.code == code)
        if is_active is not None:
            stmt = stmt.where(OauthProviderModel.is_active.is_(is_active))

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_oauth_provider_by_id(
        self, id: int, is_active: bool | None = None
    ) -> UserDTO.OauthProvider | None:
        stmt = select(OauthProviderModel).where(OauthProviderModel.id == id)
        if is_active is not None:
            stmt = stmt.where(OauthProviderModel.is_active.is_(is_active))

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def get_oauth_account_by_filter(
        self,
        oauth_provider_id: int,
        provider_user_id: str,
    ) -> UserDTO.UserOAuthAccount | None:
        uoa = UserOauthAccountModel
        stmt = select(uoa).where(
            uoa.oauth_providers_id == oauth_provider_id,
            uoa.provider_user_id == provider_user_id,
        )

        model = self._db.execute(stmt).scalar_one_or_none()
        return model.to_dto() if model else None

    def list_oauth_accounts_by_user(
        self, user_id: int, unlinked_at_is_null: bool | None = None
    ) -> list[UserDTO.UserOAuthAccount]:
        uoa = UserOauthAccountModel
        stmt = select(uoa).where(uoa.user_id == user_id)
        if unlinked_at_is_null:
            stmt = stmt.where(uoa.unlinked_at.is_(None))
        rows = self._db.execute(stmt).scalars().all()
        return [row.to_dto() for row in rows]

    def list_deleted_user(
        self, status: str | None, start_date: datetime, end_date: datetime
    ) -> list[UserDTO.User]:
        stmt = select(UserModel).where(
            UserModel.deleted_at >= start_date, UserModel.deleted_at < end_date
        )

        if status:
            stmt = stmt.where(UserModel.status == to_db_value(status))

        result = self._db.execute(stmt).scalars().all()
        return [user.to_dto() for user in result]

    def list_user_filter(
        self,
        *,
        status: str | None,
        role: str | None,
        limit: int,
        offset: int,
        deleted_is_null: bool | None = None,
    ) -> list[UserDTO.User]:
        stmt = select(UserModel)

        if status:
            stmt = stmt.where(UserModel.status == to_db_value(status))
        if role:
            stmt = stmt.where(UserModel.role == to_db_value(role))
        if deleted_is_null:
            stmt = stmt.where(UserModel.deleted_at.is_(None))

        stmt = stmt.order_by(desc(UserModel.created_at)).limit(limit).offset(offset)
        result = self._db.execute(stmt).scalars().all()
        return [user.to_dto() for user in result]

    def _to_email_verification_where_mapping(
        self, filters: EmailDTO.EmailVerificationFilter
    ):
        wheres = []
        if filters.id is not None:
            wheres.append(EmailVerificationModel.id == filters.id)
        if filters.user_id is not None:
            wheres.append(EmailVerificationModel.user_id == filters.user_id)
        if filters.statuses is not None:
            wheres.append(EmailVerificationModel.status.in_(filters.statuses))
        if filters.expires_after is not None:
            wheres.append(EmailVerificationModel.expires_at > filters.expires_after)
        if filters.expires_before is not None:
            wheres.append(EmailVerificationModel.expires_at < filters.expires_before)
        return wheres

    def _to_email_verification_values_mapping(
        self, updates: EmailDTO.EmailVerificationUpdate
    ):
        values = {}
        if updates.status is not None:
            values[EmailVerificationModel.status] = updates.status
        if updates.expires_at is not None:
            values[EmailVerificationModel.expires_at] = updates.expires_at
        if updates.sent_at is not None:
            values[EmailVerificationModel.sent_at] = updates.sent_at
        if updates.consumed_at is not None:
            values[EmailVerificationModel.consumed_at] = updates.consumed_at
        return values

    def update_user_settings(
        self, 
        user_id: int,
        is_marketing: bool | None,
        is_quiet_hours: bool | None
    ) -> int:
        values = {}
        if is_marketing is not None:
            values[UserModel.is_marketing] = is_marketing
        if is_quiet_hours is not None:
            values[UserModel.is_quiet_hours] = is_quiet_hours

        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(values)
            .execution_options(synchronize_session=False)
        )
        result = self._db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)


    def update_oauth_accounts_unlinked_at(
        self, user_id: int, *, unlinked_at: datetime
    ) -> int:
        stmt = (
            update(UserOauthAccountModel)
            .where(UserOauthAccountModel.user_id == user_id)
            .where(UserOauthAccountModel.unlinked_at.is_(None))
            .values(unlinked_at=unlinked_at)
        )
        result = self._db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    def update_email_verification_by_filter(
        self,
        filters: EmailDTO.EmailVerificationFilter,
        updates: EmailDTO.EmailVerificationUpdate,
    ) -> int:
        if filters.id is None and filters.user_id is None:
            raise ValidationAppError(
                "Unsafe update: id or user_id required", target="filters"
            )
        where = self._to_email_verification_where_mapping(filters)
        if not where:
            raise ValidationAppError(
                "Unsafe update: at least one narrowing filter required",
                target="filters",
            )
        values = self._to_email_verification_values_mapping(updates)
        if not values:
            return 0

        result = self._db.execute(
            update(EmailVerificationModel)
            .where(*where)
            .values(values)
            .execution_options(synchronize_session=False)
        )

        return int(getattr(result, "rowcount", 0) or 0)

    def update_password_reset_by_filter(
        self,
        *,
        id: int,
        expires_after: datetime | None = None,
        sent_at: datetime | None = None,
        consumed_at: datetime | None = None,
        sent_is_null: bool | None = None,
        consumed_is_null: bool | None = None,
    ) -> int:
        wheres = []
        wheres.append(PasswordResetModel.id == id)

        if expires_after is not None:
            wheres.append(PasswordResetModel.expires_at > expires_after)

        if sent_is_null:
            wheres.append(PasswordResetModel.sent_at.is_(None))

        if consumed_is_null:
            wheres.append(PasswordResetModel.consumed_at.is_(None))

        if not wheres:
            raise ValidationAppError(
                "Unsafe update: at least one narrowing filter required",
                target="filters",
            )

        values = {}
        if sent_at is not None:
            values[PasswordResetModel.sent_at] = sent_at
        if consumed_at is not None:
            values[PasswordResetModel.consumed_at] = consumed_at

        if not values:
            return 0

        stmt = (
            update(PasswordResetModel)
            .where(*wheres)
            .values(values)
            .execution_options(synchronize_session=False)
        )

        result = self._db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    def update_user_password_hash(self, id: int, password_hash: str) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values({UserModel.password_hash: password_hash})
            .execution_options(synchronize_session=False)
        )
        self._db.execute(stmt)

    def update_user_last_login_at(
        self, id: int, last_login_at: datetime | None = None
    ) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values({UserModel.last_login_at: last_login_at})
            .execution_options(synchronize_session=False)
        )
        self._db.execute(stmt)

    def update_user_email_verified_at(
        self, id: int, email_verified_at: datetime | None = None
    ) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values({UserModel.email_verified_at: email_verified_at})
            .execution_options(synchronize_session=False)
        )
        self._db.execute(stmt)

    def update_user_email(
        self,
        id: int,
        email_fingerprint: bytes | None = None,
        email_ciphertext: bytes | None = None,
        email_nonce: bytes | None = None,
        email_key_version: int | None = None,
    ) -> None:
        stmt = (
            update(UserModel)
            .where(UserModel.id == id)
            .values(
                email_fingerprint=email_fingerprint,
                email_ciphertext=email_ciphertext,
                email_nonce=email_nonce,
                email_key_version=email_key_version,
            )
            .execution_options(synchronize_session=False)
        )

        self._db.execute(stmt)

    def update_user_emails(self, user_email_updates: list[UserDTO.UserEmailInfo]):
        formatted_data = [
            {
                "b_id": d["id"],
                "b_nickname": d.get("nickname"),
                "b_fingerprint": d.get("email_fingerprint"),
                "b_ciphertext": d.get("email_ciphertext"),
                "b_nonce": d.get("email_nonce"),
                "b_key_version": d.get("email_key_version"),
                "b_verified_at": d.get("email_verified_at"),
            }
            for d in [item.to_dict(include_none=True) for item in user_email_updates]
        ]

        # No primary key value supplied for column(s) users.id; per-row ORM Bulk UPDATE by Primary Key requires that records contain primary key values
        # 세션 동기화 로직으로 인해 PK 확인 에러가 발생함.
        # 이를 회피하기 위해 ORM 계층을 건너뛰는 __table__ 기반의 SQL Expression Language 사용. 한마디로 ORM 개억까. 이런것도 안될거면 왜 쓰는거야
        stmt = (
            update(UserModel.__table__)
            .where(UserModel.__table__.c.id == bindparam("b_id"))
            .values(
                nickname=bindparam("b_nickname"),
                email_fingerprint=bindparam("b_fingerprint"),
                email_ciphertext=bindparam("b_ciphertext"),
                email_nonce=bindparam("b_nonce"),
                email_key_version=bindparam("b_key_version"),
                email_verified_at=bindparam("b_verified_at"),
            )
        )

        self._db.execute(stmt, formatted_data)

    def delete_user(
        self, user_id: int, *, status: UserStatus, deleted_at: datetime
    ) -> int:
        stmt = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .where(UserModel.deleted_at.is_(None))
            .values(status=to_db_value(status), deleted_at=deleted_at)
            .execution_options(synchronize_session=False)
        )
        result = self._db.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    def delete_user_oauth_accounts(
        self,
        user_ids: list[int],
    ):
        if not user_ids:
            return

        stmt = (
            delete(UserOauthAccountModel)
            .where(UserOauthAccountModel.user_id.in_(user_ids))
            .execution_options(synchronize_session=False)
        )

        self._db.execute(stmt)
