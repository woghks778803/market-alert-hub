from fastapi import HTTPException
from app.service.unit_of_work import UnitOfWork
from app.core import create_access_token, verify_password

class AuthService:
    """인증 유즈케이스: 회원가입/로그인/JWT 발급."""
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def register(self, email: str, password: str):
        try:
            # 중복 체크는 Repo 레벨에서 Unique 제약으로 보장(IntegrityError 핸들러로 처리)
            user = self.uow.users.create(email, password)
            self.uow.commit()
            return user
        except Exception:
            self.uow.rollback()
            raise

    def login(self, email: str, password: str) -> str:
        user = self.uow.users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        return create_access_token(user.email)
