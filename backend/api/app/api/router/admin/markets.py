from datetime import datetime
from fastapi import APIRouter, Depends, Body, Request, Response, status, Security, Path, Query

from app.api.deps import get_current_user, get_services, get_request_meta, RequestMeta
from app.api.common.envelope import Envelope, ok, created
from app.api.schema import AuthSchema, MarketSchema
from app.service.sync.factory import ServiceFactory
import app.api.openapi as OpenApi

router = APIRouter(prefix="/markets")

@router.post(
    "/backfill-requests",
    response_model=Envelope[MarketSchema.SimpleOk],
    summary="백필 요청 등록",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[MarketSchema.SimpleOk],  
            description="백필 요청 성공",
        ),
    ),
)
def create_backfill_request(
    response: Response,
    payload: MarketSchema.BackfillRequestIn,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.markets.create_backfill_request(
        user_id=user.id,
        exchange_instrument_ids=payload.exchange_instrument_ids,
        base=payload.base,
        start_at=payload.start_at,
        end_at=payload.end_at,
        reason=payload.reason,
    )

    return created(
        {"ok": True},
        response=response,
        request_id=meta.request_id,
        location=f"/markets/backfill-requests/{result.id}",
    )