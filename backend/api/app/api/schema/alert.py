from pydantic import BaseModel

class AlertCreate(BaseModel):
    exchange: str
    symbol: str
    target_price: float
    direction: str  # "above" | "below"

class AlertRead(AlertCreate):
    id: int
    status: str

    class Config:
        from_attributes = True
