from app.service.uow import UnitOfWork
from app.infra.db.model import User

class UserService:
    """사용자 조회/수정 등 유즈케이스."""
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def get_by_email(self, email: str) -> User | None:
        return self.uow.users.get_by_email(email)
