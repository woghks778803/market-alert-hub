from fastapi import APIRouter
from app.core.market_registry import registry

# TODO: 테스트 목적 임시
import app.api.adapters.market.upbit  
import app.api.adapters.market.binance  

router = APIRouter(prefix="/meta")

@router.get("/exchanges")
def list_exchanges():
    return {"items": registry.list()}
