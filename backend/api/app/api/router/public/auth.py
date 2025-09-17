from fastapi import APIRouter, Depends, Body, Security, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user_email
from app.service import ServiceFactory

import app.api.schema as pschema
import app.api.openapi as popenapi

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses=popenapi.combine(popenapi.ERR_401, popenapi.ERR_500),
)

def get_services(db: Session = Depends(get_db)) -> ServiceFactory:
    return ServiceFactory(db)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=pschema.UserRead,
    summary="유저 회원가입",
    description="이메일 중복 시 `ConflictError`로 처리됩니다(전역 핸들러가 409 반환).",
    responses=popenapi.combine(
        popenapi.CREATED(pschema.UserRead, description="회원가입 성공",
                example={"id": 1, "email": "alice@example.com"}),
        popenapi.ERR_400, popenapi.ERR_409,
    ),
)
def register(
    payload: pschema.UserCreate = Body(
        ...,
        example={"email": "alice@example.com", "password": "P@ssw0rd!"},
    ),
    svcs: ServiceFactory = Depends(get_services),
):
    """
    - 중복 이메일: `ConflictError` 발생(서비스에서 raise) → 전역 핸들러가 JSON 에러 포맷으로 응답
    - 기타 유효성: FastAPI의 `RequestValidationError` 또는 `ValidationAppError`
    """
    # 서비스가 내부에서 중복체크 후 ConflictError(or IntegrityError) 발생시킴
    return svcs.auth().register(payload.email, payload.password)


@router.post(
    "/login",
    response_model=pschema.TokenPair,
    summary="로그인 (JWT 발급)",
    description="이메일/비밀번호가 틀리면 `AuthError`(401)로 처리됩니다.",
    responses=popenapi.combine(
        popenapi.OK(pschema.TokenPair, description="로그인 성공",
           example={"access_token": "<jwt>", "token_type": "bearer"}),
        popenapi.ERR_400, popenapi.ERR_401,
    ),
)
def login(
    payload: pschema.UserLogin = Body(
        ...,
        example={"email": "alice@example.com", "password": "P@ssw0rd!"},
    ),
    svcs: ServiceFactory = Depends(get_services),
):
    # 서비스가 인증 실패 시 AuthError(status=401, code='unauthorized')를 raise
    token = svcs.auth().login(payload.email, payload.password)
    return {"access_token": token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=pschema.UserRead,
    summary="내 프로필 조회",
    description="우상단 **Authorize**로 JWT 설정 후 호출하세요.",
    responses=popenapi.combine(
        popenapi.OK(pschema.TokenPair, description="성공",
           example={"access_token": "<jwt>", "token_type": "bearer"}),
        popenapi.ERR_400, popenapi.ERR_401, popenapi.ERR_404
    ),
)
def me(
    email: str = Security(get_current_user_email),  # 🔒 Swagger에 보안 표시
    svcs: ServiceFactory = Depends(get_services),
):
    user = svcs.users().get_by_email(email)
    if not user:
        from app.domain import NotFoundError
        raise NotFoundError(message="User not found", target="email")
    return user
