from fastapi import Response, APIRouter, status, Depends
from app.core.constants import CandleBaseInterval

from app.api.deps import get_services, get_request_meta, RequestMeta
from app.api.schema import SeedSchema
from app.api.common.envelope import Envelope, ok, created
from app.service.sync.factory import ServiceFactory
import app.api.openapi as OpenApi

router = APIRouter(prefix="/seed/snapshots")

# @router.post(
#     "/{base}",
#     status_code=status.HTTP_201_CREATED,
#     response_model=Envelope[SeedSchema.CreateOk],
#     summary="캔들 스냅샷 저장",
#     description="지정한 기준 간격(1m/1h/1d)의 캔들 스냅샷을 배치로 저장합니다.",
#     responses=OpenApi.combine(
#         OpenApi.OK(
#             Envelope[SeedSchema.CreateOk],
#             description="시드 저장 성공",
#             example=OpenApi.wrap_example({"requested_base": "1h", "requested_count": 73200}),
#         ),
#     ),
# )
# def seed_price_snapshots(
#     response: Response,
#     base: CandleBaseInterval,
#     svcs: ServiceFactory = Depends(get_services),
#     meta: RequestMeta = Depends(get_request_meta),
# ):
#     """
#     개발/테스트용: price_snapshots_{interval} 테이블에 시드 데이터 삽입
#     """
#     result = svcs.markets.seed_snapshots(base=base)
#     return created(SeedSchema.CreateOk(requested_count=result, requested_base=base), response=response, request_id=meta.request_id)
