from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class AlertCreate(BaseModel):
    exchange_id: int
    symbol: str
    target_price: float
    direction: Literal["above", "below"]

class AlertRead(BaseModel):
    id: int
    exchange_id: int
    exchange_code: str | None = None  # 조인 결과로 채움(Exchange.code)
    symbol: str
    target_price: float
    direction: Literal["above", "below"]
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
