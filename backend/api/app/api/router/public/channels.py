from fastapi import APIRouter, Depends, Body, Request, Response, status, Security, Path, Query

from app.service.factory import ServiceFactory
from app.api.schema import AuthSchema, ChannelSchema
from app.api.common.envelope import Envelope, ok, created, no_content
from app.api.deps import get_current_user, get_services, get_request_meta, RequestMeta
import app.api.openapi as OpenApi

router = APIRouter(prefix="/channels")


# @router.get(
#     "",
#     response_model=Envelope[list[ChannelSchema.ChannelRead]],
#     summary="채널 목록",
#     responses=OpenApi.combine(
#         OpenApi.OK(
#             Envelope[list[ChannelSchema.ChannelRead]],  #  스키마도 래퍼로
#             description="리스트 조회 성공",
#         ),
#         OpenApi.ERR_409,
#     ),
# )
# def list_channels(
#     limit: int = Query(10, ge=1, le=20),
#     offset: int = Query(0, ge=0),
#     user: AuthSchema.CurrentUser = Security(get_current_user),
#     svcs: ServiceFactory = Depends(get_services),
#     meta: RequestMeta = Depends(get_request_meta),
# ):
#     rows = svcs.channels.list_channel_by_filter(limit=limit, offset=offset)
#     return ok(rows, request_id=meta.request_id)


# @router.get(
#     "/{user_channel_id}",
#     response_model=Envelope[ChannelSchema.ChannelRead],
#     summary="사용자 채널 상세",
#     responses=OpenApi.combine(
#         OpenApi.OK(Envelope[ChannelSchema.ChannelRead]),
#     ),
# )
# def get_channel(
#     user_channel_id: int = Path(..., ge=1),
#     svcs: ServiceFactory = Depends(get_services),
#     meta: RequestMeta = Depends(get_request_meta),
# ):
#     result = svcs.channels.get_by_channel_id(user_channel_id=user_channel_id)
#     out = ChannelSchema.ChannelRead.model_validate(result)
#     return ok(out, request_id=meta.request_id)

