from fastapi import APIRouter, status, Depends
from decimal import Decimal
from app.core.constants import CandleBaseInterval

from app.api.deps import get_services
from app.service.factory import ServiceFactory

router = APIRouter(prefix="/seed/snapshots")

@router.post(
    "/{base}",
    status_code=status.HTTP_201_CREATED,
    # response_model=MarketSchema.CandleIngestResult,
    summary="캔들 스냅샷 저장",
    description="지정한 기준 간격(1m/1h/1d)의 캔들 스냅샷을 배치로 저장합니다.",
    # responses=OpenApi.combine(
    #     OpenApi.CREATED(
    #         MarketSchema.CandleIngestResult, 
    #         description="저장 성공",
    #         example={"id": 12345, "created": True}
    #     ),
    #     OpenApi.ERR_400, OpenApi.ERR_409,
    # ),
)
def seed_price_snapshots(
    base: CandleBaseInterval | None ,
    svcs: ServiceFactory = Depends(get_services),
):
    """
    개발/테스트용: price_snapshots_{interval} 테이블에 시드 데이터 삽입
    """
    return svcs.markets().seed_snapshots(base=base)
