from typing import Callable
from app.service.uow import UnitOfWork
from app.infra.db.model import UserModel
from app.domain.errors import ValidationAppError, NotFoundError
from datetime import datetime, timezone
from app.core.constants import UserStatus, UserRole

class UserService:
    def __init__(
        self,
        *,
        uow_factory: Callable[[], UnitOfWork],
    ) -> None:
        self._uow_factory = uow_factory

    def coerce(self, value, EnumClass, target_name):
        if value is None or isinstance(value, EnumClass):
            return value
        try:
            return EnumClass(str(value))
        except ValueError:
            raise ValidationAppError(f"Invalid {target_name}", target=target_name)
        
    def get_by_email(self, email: str) -> UserModel | None:
        with self._uow_factory() as uow: 
            return uow.users.get_by_email(email)

    def _ensure_user(self, uow: UnitOfWork, user_id: int):
        user = uow.users.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", target="user_id")  # 전역핸들러에서 404 매핑되게
        return user

    def list(self, *, status: UserStatus | None, role: UserRole | None, limit: int, offset: int):
        role = self.coerce(role, UserRole, "role")
        status = self.coerce(status, UserStatus, "status")

        with self._uow_factory() as uow:
            rows = uow.users.list(status=status, role=role, limit=limit, offset=offset)
            return rows

    def get_by_id(self, *, user_id: int) -> UserModel:
        with self._uow_factory() as uow:
            return self._ensure_user(uow, user_id)

    def update(self, *, user_id: int, role: UserRole | None, status: UserStatus | None):
        role = self.coerce(role, UserRole, "role")
        status = self.coerce(status, UserStatus, "status")

        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)
            if role is not None:
                user.role = role
            if status is not None:
                user.status = status
            user.updated_at = datetime.now(timezone.utc) if hasattr(user, "updated_at") else getattr(user, "updated_at", None)
            uow.commit()
            return user

    def delete(self, *, user_id: int) -> None:
        with self._uow_factory() as uow:
            user = self._ensure_user(uow, user_id)
            user.status = UserStatus.DELETED
            if hasattr(user, "is_valid"):
                user.is_valid = False
            uow.commit()
