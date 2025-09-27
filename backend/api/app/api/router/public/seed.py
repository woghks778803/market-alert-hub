from fastapi import APIRouter, Depends, Body, Query
from datetime import datetime
from decimal import Decimal
from typing import Literal
from app.core.constants import CandleBaseInterval

from app.api.deps import get_services
from app.service.factory import ServiceFactory

router = APIRouter(prefix="/seed/snapshots", tags=["SeedSnapshots"])

@router.post("/{base}")
def seed_price_snapshots(
    base: CandleBaseInterval | None ,
    exchange_instrument_id: int = Body(..., embed=True),
    ts_open: datetime = Body(..., embed=True),
    open: Decimal = Body(..., embed=True),
    high: Decimal = Body(..., embed=True),
    low: Decimal = Body(..., embed=True),
    close: Decimal = Body(..., embed=True),
    volume: Decimal = Body(..., embed=True),
    svcs: ServiceFactory = Depends(get_services),
):
    """
    개발/테스트용: price_snapshots_{interval} 테이블에 시드 데이터 삽입
    - interval: "1m" | "1h" | "1d"
    """
    return svcs.markets().seed_snapshot(
        base=base,
        exchange_instrument_id=exchange_instrument_id,
        ts_open=ts_open,
        open=open,
        high=high,
        low=low,
        close=close,
        volume=volume,
    )
