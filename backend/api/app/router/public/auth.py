from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.db import get_db
from app.core.security import create_access_token
from app.repository import SqlUserRepo
from app.schema.auth import (
    TokenPair, ErrorResponse
)
from app.schema.user import (
    UserCreate, UserLogin, UserRead
)


# 보호된 엔드포인트 예시용
from fastapi import Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post(
    "/register",
    status_code=201,
    response_model=UserRead,
    summary="회원가입",
    description="이메일/비밀번호로 신규 사용자를 생성합니다.",
    responses={
        201: {"description": "생성됨"},
        409: {"model": ErrorResponse, "description": "이메일 중복"},
        422: {"description": "검증 오류 (Pydantic)"},
    },
)
def register(
    payload: UserCreate = Body(
        ...,
        examples={
            "normal": {
                "summary": "정상 예시",
                "value": {"email": "user@example.com", "password": "S3cret!"},
            }
        },
    ),
    db: Session = Depends(get_db),
):
    repo = SqlUserRepo(db)
    try:
        return repo.create(payload.email, payload.password)
    except IntegrityError:
        # 유니크 제약(이메일) 충돌
        raise HTTPException(status_code=409, detail="Email already exists")

@router.post(
    "/login",
    response_model=TokenPair,
    summary="로그인 (JWT 발급)",
    description="자격 증명이 유효하면 액세스 토큰(JWT)을 발급합니다.",
    responses={
        200: {
            "description": "성공",
            "content": {
                "application/json": {
                    "examples": {
                        "ok": {
                            "summary": "성공 예시",
                            "value": {
                                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                "token_type": "bearer",
                            },
                        }
                    }
                }
            },
        },
        400: {"model": ErrorResponse, "description": "이메일 또는 비밀번호 불일치"},
    },
)
def login(
    payload: UserLogin = Body(
        ...,
        examples={
            "normal": {
                "summary": "정상 예시",
                "value": {"email": "user@example.com", "password": "S3cret!"},
            }
        },
    ),
    db: Session = Depends(get_db),
):
    repo = SqlUserRepo(db)
    user = repo.authenticate(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

# JWT Authorize 버튼 동작 데모용 보호 엔드포인트
@router.get(
    "/me",
    response_model=UserRead,
    summary="내 정보 (인증 필요)",
    description="Swagger에서 **Authorize** 버튼으로 토큰을 설정한 뒤 호출하세요.",
    responses={401: {"model": ErrorResponse, "description": "인증 실패"}},
)
def me(
    creds: HTTPAuthorizationCredentials | None = Security(bearer),
    db: Session = Depends(get_db),
):
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    # 토큰의 sub(email)로 사용자 조회하는 로직이 있다면 사용
    # 여기서는 간단히 데모로 email을 토큰 payload에서 복호화해서 가져왔다고 가정해도 됨.
    # 실제 구현에서는 verify + decode 후 repo.get_by_email 사용.
    raise HTTPException(status_code=501, detail="Implement token decode & fetch user")  # TODO
