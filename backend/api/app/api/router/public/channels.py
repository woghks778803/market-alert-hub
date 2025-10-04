from fastapi import APIRouter, Depends, Body, Request, Response, status, Security, Path

from app.core.auth import token_hash
from app.infra.db.model import UserModel
from app.service.factory import ServiceFactory
from app.api.schema import ChannelSchema
from app.api.common.envelope import Envelope, ok, created, no_content
from app.api.deps import get_current_token, get_current_user, get_services, get_request_meta, RequestMeta
import app.api.openapi as OpenApi

router = APIRouter(prefix="/channels")

@router.get(
    "", 
    response_model=Envelope[list[ChannelSchema.ChannelRead]],
    summary="사용자 채널 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[ChannelSchema.ChannelRead]],  # ✅ 스키마도 래퍼로
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_channels(
    current_user=Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.channels().list(user_id=current_user.id)
    return ok(rows, request_id=meta.request_id)

@router.get(
    "/{user_channel_id}", 
    response_model=Envelope[ChannelSchema.ChannelRead], 
    summary="사용자 채널 상세",
    responses=OpenApi.combine(
        OpenApi.OK(Envelope[ChannelSchema.ChannelRead]),
    ),
)
def get_channels(
    user_channel_id: int = Path(..., ge=1),
    current_user=Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.channels().get_by_id(user_channel_id=user_channel_id)
    return ok(result, request_id=meta.request_id)

@router.post(
    "", 
    response_model=Envelope[ChannelSchema.ChannelRead],
    summary="사용자 채널 등록",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[list[ChannelSchema.ChannelRead]],  # ✅ 스키마도 래퍼로
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def create_channel(
    response: Response,
    payload : ChannelSchema.ChannelCreate = Body(...,),
    current_user=Depends(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.channels().create(
        user_id=current_user.id, provider_id=payload.channel_provider_id, config=payload.config
    )
    return created(result, response=response, request_id=meta.request_id)

@router.delete(
    "/{user_channel_id}", 
    summary="사용자 채널 삭제(soft)",
    responses=OpenApi.combine(
        OpenApi.NO_CONTENT({}, description="완료")
    ),
)
def delete_channel(
    user_channel_id: int = Path(..., ge=1),
    svcs: ServiceFactory = Depends(get_services),
):
    svcs.channels().delete_channel(user_channel_id=user_channel_id)
    return no_content()