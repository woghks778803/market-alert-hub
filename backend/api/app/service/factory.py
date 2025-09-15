from sqlalchemy.orm import Session
from app.service.unit_of_work import UnitOfWork
from app.service.auth_service import AuthService
from app.service.user_service import UserService

class ServiceFactory:
    """라우터에서 서비스 생성 경로를 단일화."""
    def __init__(self, db: Session) -> None:
        self.uow = UnitOfWork(db)

    def auth(self) -> AuthService:
        return AuthService(self.uow)

    def users(self) -> UserService:
        return UserService(self.uow)
