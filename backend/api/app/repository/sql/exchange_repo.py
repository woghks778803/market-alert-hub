from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from app.infra.db.model import Exchange

class SqlExchangeRepo:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, ex_id:int) -> Optional[Exchange]: 
        return self._db.get(Exchange, ex_id)
    
    def get_code_by_id(self, ex_id:int) -> Optional[str]:
        return self._db.execute(
            select(Exchange.code).where(Exchange.id==ex_id)
        ).scalar_one_or_none()