# app/api/router/public/auth.py
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Body, Request, status, Header, HTTPException
from sqlalchemy.orm import Session as DbSession

import app.api.openapi as OpenApi
from app.api.schema import UserSchema, AuthSchema
from app.api.deps import get_db 

from app.service.uow import UnitOfWork
from app.service.factory import ServiceFactory

from app.core.auth import decode_token, token_hash 

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses=OpenApi.combine(OpenApi.ERR_401, OpenApi.ERR_500),
)

def get_services(db: DbSession = Depends(get_db)) -> ServiceFactory:
    # Factory는 uow_factory만 받는다. 세션은 여기서만 알고 끝.
    return ServiceFactory(lambda: UnitOfWork(db, owns_session=False))


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSchema.UserReadPublic,
    summary="유저 회원가입",
    description="이메일 중복 시 ConflictError로 처리(전역 핸들러에서 409로 매핑).",
    responses=OpenApi.combine(
        OpenApi.CREATED(UserSchema.UserReadPublic, description="회원가입 성공",
                         example={"id": 1, "email": "alice@example.com"}),
        OpenApi.ERR_400, OpenApi.ERR_409,
    ),
)
def register(
    request: Request,
    payload: UserSchema.UserCreatePublic = Body(..., example={
        "email": "alice@example.com",
        "nickname": "Alice",
        "password": "P@ssw0rd!"
    }),
    svcs: ServiceFactory = Depends(get_services),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return svcs.auths().register(email=payload.email, nickname=payload.nickname, password=payload.password, ip=ip, ua=ua)


@router.post(
    "/login",
    response_model=AuthSchema.TokenOut,
    summary="로그인 (JWT 발급)",
    responses=OpenApi.combine(OpenApi.OK(AuthSchema.TokenOut, description="로그인 성공"), OpenApi.ERR_400, OpenApi.ERR_401),
)
def login(
    request: Request,
    payload: AuthSchema.Login = Body(..., example={"email": "alice@example.com", "password": "P@ssw0rd!"}),
    svcs: ServiceFactory = Depends(get_services),
):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return svcs.auths().login(email=payload.email, password=payload.password, ip=ip, ua=ua)


@router.post(
    "/logout",
    response_model=AuthSchema.SimpleOk,
    summary="로그아웃 (세션 무효화)",
    responses=OpenApi.combine(OpenApi.OK(AuthSchema.SimpleOk, description="로그아웃 성공"), OpenApi.ERR_401),
)
def logout(
    authorization: Optional[str] = Header(None, description="Bearer <JWT>"),
    svcs: ServiceFactory = Depends(get_services),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    jwt = authorization.split(" ", 1)[1].strip()
    return svcs.auths().logout(token_hash=token_hash(jwt))


@router.get(
    "/me",
    response_model=UserSchema.MeRead,
    summary="내 정보 조회",
    responses=OpenApi.combine(OpenApi.OK(UserSchema.MeRead, description="내 정보"), OpenApi.ERR_401, OpenApi.ERR_404),
)
def me(
    authorization: Optional[str] = Header(None, description="Bearer <JWT>"),
    svcs: ServiceFactory = Depends(get_services),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    jwt = authorization.split(" ", 1)[1].strip()
    claims = decode_token(jwt)  # sub = user.id 규약
    user_id = int(claims["sub"])
    return svcs.auths().me(user_id=user_id)
