from fastapi import Response, APIRouter, Depends, Query, Security

from app.core.constants import AlertStatus, AlertSort
from app.api.deps import get_current_user, get_services, get_request_meta, RequestMeta
from app.api.schema import AuthSchema, AlertSchema
from app.api.common.envelope import Envelope, ok, created
from app.service.factory import ServiceFactory
import app.api.openapi as OpenApi

router = APIRouter(prefix="/alerts")

@router.get(
    "/{alert_id:int}",
    response_model=Envelope[AlertSchema.AlertRead],
    summary="알림 상세 정보",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AlertSchema.AlertRead],
            description="알림 조회 성공",
        ),
        OpenApi.ERR_404,
    ),
)
def get_alert(
    alert_id: int,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    row = svcs.alerts.get_by_user_alert(
        user_id=user.id,
        alert_id=alert_id,
    )

    return ok(row, request_id=meta.request_id)  

@router.get(
    "/types",
    response_model=Envelope[list[AlertSchema.AlertTypeRead]],
    summary="알림 타입 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[AlertSchema.AlertTypeRead]],  
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_types(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: str | None = Query(None),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.alerts.list_type_by_filter(
        search=search,
        limit=limit, 
        offset=offset
    )
    return ok(rows, request_id=meta.request_id)

@router.get(
    "",
    response_model=Envelope[list[AlertSchema.AlertRead]],
    summary="알림 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[AlertSchema.AlertRead]],
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_alert(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: AlertStatus | None = Query(None),
    sort: AlertSort | None = Query(None),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.alerts.list_alert_by_filter(
        user_id=user.id,
        status=status,
        sort=sort,
        limit=limit,
        offset=offset,
    )

    return ok(rows, request_id=meta.request_id)

@router.get(
    "/archives",
    response_model=Envelope[list[AlertSchema.AlertRead]],
    summary="알림 보관 목록",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[list[AlertSchema.AlertRead]],
            description="리스트 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def list_archived_alert(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: AlertSort | None = Query(None),
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    rows = svcs.alerts.list_alert_by_filter(
        user_id=user.id,
        sort=sort,
        archived_only=True,
        limit=limit,
        offset=offset,
    )

    return ok(rows, request_id=meta.request_id)

@router.get(
    "/summary",
    response_model=Envelope[AlertSchema.AlertSummaryRead],
    summary="알림 요약",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AlertSchema.AlertSummaryRead],
            description="요약 조회 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def get_alert_summary(
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.alerts.get_alert_summary(
        user_id=user.id,
    )

    return ok(result, request_id=meta.request_id)

@router.post(
    "",
    response_model=Envelope[AlertSchema.SimpleOk],
    summary="사용자 알림 등록",
    description="",
    responses=OpenApi.combine(
        OpenApi.CREATED(
            Envelope[AlertSchema.SimpleOk],
            description="등록 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def create_alert(
    response: Response,
    payload: AlertSchema.AlertIn,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.alerts.create_alert(
        user_id=user.id,
        name=payload.name,
        exchange_instrument_id=payload.exchange_instrument_id,
        alert_type_id=payload.alert_type_id,
        is_once=payload.is_once,
        status=payload.status,
        throttle_timeframe=payload.throttle_timeframe,
        timezone=payload.timezone,
        use_validity=payload.use_validity,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,

        timeframe=payload.timeframe,  
        period=payload.period,       

        params=payload.params,
    )

    return created(
        {"ok": True},
        response=response,
        request_id=meta.request_id,
        location=f"/alert/{result.id}",
    )

@router.patch(
    "/{alert_id}",
    response_model=Envelope[AlertSchema.SimpleOk],
    summary="사용자 알림 수정",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AlertSchema.SimpleOk],
            description="알림 수정 성공",
        ),
        OpenApi.ERR_404,
        OpenApi.ERR_409,
    ),
)
def change_alert(
    alert_id: int,
    payload: AlertSchema.AlertIn,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    row = svcs.alerts.change_alert(
        alert_id=alert_id,

        user_id=user.id,
        name=payload.name,
        exchange_instrument_id=payload.exchange_instrument_id,
        alert_type_id=payload.alert_type_id,
        is_once=payload.is_once,
        status=payload.status,
        throttle_timeframe=payload.throttle_timeframe,
        timezone=payload.timezone,
        use_validity=payload.use_validity,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,

        timeframe=payload.timeframe,
        period=payload.period,

        params=payload.params,
    )

    return ok(row, request_id=meta.request_id)

@router.patch(
    "/{alert_id}/status",
    response_model=Envelope[AlertSchema.SimpleOk],
    summary="알림 상태 변경",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AlertSchema.SimpleOk],
            description="변경 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def change_alert_status(
    alert_id: int,
    payload: AlertSchema.AlertStatusIn,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.alerts.change_alert_status(
        user_id=user.id,
        alert_id=alert_id,
        status=payload.status,
    )

    return ok(result, request_id=meta.request_id)


@router.delete(
    "/{alert_id:int}",
    response_model=Envelope[AlertSchema.SimpleOk],
    summary="알림 삭제",
    responses=OpenApi.combine(
        OpenApi.OK(
            Envelope[AlertSchema.SimpleOk],
            description="삭제 성공",
        ),
        OpenApi.ERR_409,
    ),
)
def delete_alert(
    alert_id: int,
    user: AuthSchema.CurrentUser = Security(get_current_user),
    svcs: ServiceFactory = Depends(get_services),
    meta: RequestMeta = Depends(get_request_meta),
):
    result = svcs.alerts.delete_alert(
        user_id=user.id,
        alert_id=alert_id,
    )

    return ok(result, request_id=meta.request_id)