from typing import Sequence, Iterable
from sqlalchemy import select, update, desc, and_
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import UserModel, EmailVerificationModel
from app.core.util.datetime import utcnow
from app.core.constants import EmailVerificationStatus
from app.domain import EmailDTO, ValidationAppError
from ._utils import to_db_value
from ..protocol.user_repo import UserRepo
from datetime import datetime 

class SqlUserRepo(UserRepo):

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add_user(self, user: UserModel) -> UserModel:
        self._db.add(user); self._db.flush(); return user
    
    def add_email_verification(self, email_verification: EmailVerificationModel) -> EmailVerificationModel:
        self._db.add(email_verification); self._db.flush(); return email_verification

    def get_user_by_email_fingerprint(self, email_fingerprint: bytes) -> UserModel | None:
        stmt = (
            select(UserModel).where(UserModel.email_fingerprint == email_fingerprint)
        )
        result = self._db.execute(stmt).scalar_one_or_none()
        return result is not None and result
    
    def get_by_user_id(self, user_id: int) -> UserModel | None:
        stmt = select(UserModel).where(and_(UserModel.is_deleted.is_(False), UserModel.id == user_id))
        return self._db.execute(stmt).scalar_one_or_none()
    
    def get_email_verification_by_id(self, email_verification_id: int) -> EmailVerificationModel | None:
        stmt = select(EmailVerificationModel).where(EmailVerificationModel.id == email_verification_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_email_verification_by_token_hash(self, token_hash: bytes) -> EmailVerificationModel | None:
        stmt = select(EmailVerificationModel).where(EmailVerificationModel.token_hash == token_hash)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_users_filter(self, *, status: str | None, role: str | None, limit: int, offset: int) -> Sequence[UserModel]:
        stmt = select(UserModel).where(UserModel.is_deleted.is_(False))
        if status:
            stmt = stmt.where(UserModel.status == to_db_value(status))
        if role:
            stmt = stmt.where(UserModel.role == to_db_value(role))

        stmt = stmt.order_by(desc(UserModel.created_at)).limit(limit).offset(offset)
        return self._db.execute(stmt).scalars().all()


    def update_email_verifications_status_by_user_id(
        self,
        user_id: int,
        *,
        from_statuses: Iterable[EmailVerificationStatus],
        to_status: EmailVerificationStatus,
        set_expires_at: datetime,
        set_expires_at_to_now: bool = True,
        only_not_expired: bool = True,
    ) -> int:
        """
        user_id 기준으로 특정 상태(from_statuses)의 email_verifications를 일괄 업데이트한다.

        - 기본 의도: (PENDING, SENT) -> CANCELLED 로 바꾸고, expires_at을 now로 당겨 즉시 무효화
        - SELECT 없이 UPDATE 1회로 처리됨
        - 반환값: 영향을 받은 row 수
        """

        stmt = (
            update(EmailVerificationModel)
            .where(EmailVerificationModel.user_id == user_id)
            .where(EmailVerificationModel.status.in_(list(from_statuses)))
        )

        if only_not_expired:
            stmt = stmt.where(EmailVerificationModel.expires_at > set_expires_at)

        values: dict = {"status": to_status}
        if set_expires_at_to_now:
            values["expires_at"] = set_expires_at

        stmt = stmt.values(**values)

        # synchronize_session=False: 세션에 로딩된 엔티티 동기화 안 함(성능/안전)
        result = self._db.execute(stmt.execution_options(synchronize_session=False))
        return int(getattr(result, "rowcount", 0) or 0)

    def _to_email_verification_where_mapping(self, filters: EmailDTO.EmailVerificationFilter):
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

    def _to_email_verification_values_mapping(self, updates: EmailDTO.EmailVerificationUpdate):
        values = {}
        if updates.status is not None:
            values[EmailVerificationModel.status] = updates.status
        if updates.expires_at is not None:
            values[EmailVerificationModel.expires_at] = updates.expires_at
        if updates.sent_at is not None:
            values[EmailVerificationModel.sent_at] = updates.sent_at
        return values

    def update_email_verification_by_filter(
        self,
        filters: EmailDTO.EmailVerificationFilter,
        updates: EmailDTO.EmailVerificationUpdate,
    ) -> int:
        if filters.id is None and filters.user_id is None: raise ValidationAppError("Unsafe update: id or user_id required", target="filters")
        where = self._to_email_verification_where_mapping(filters)
        if not where: raise ValidationAppError("Unsafe update: at least one narrowing filter required", target="filters")
        values = self._to_email_verification_values_mapping(updates)
        if not values: return 0 

        result = self._db.execute(
            update(EmailVerificationModel)
            .where(*where)
            .values(values)
            .execution_options(synchronize_session=False)
        )

        return int(getattr(result, "rowcount", 0) or 0)