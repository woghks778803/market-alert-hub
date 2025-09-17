from app.service.uow import UnitOfWork
from app.core.auth import create_access_token, verify_password
from app.domain import AuthError

class AuthService:
    """인증 유즈케이스: 회원가입/로그인/JWT 발급."""
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def register(self, email: str, password: str):
        with self.uow as u:
            user = u.users.create(email, password)
            u.commit()
            return user

    def login(self, email: str, password: str) -> str:
        user = self.uow.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid credentials")
        return create_access_token(user.id)
