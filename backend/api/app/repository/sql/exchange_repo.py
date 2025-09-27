from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession
from typing import Optional
from app.infra.db.model import ExchangeModel

class SqlExchangeRepo:
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def get_by_id(self, ex_id:int) -> Optional[ExchangeModel]: 
        return self._db.get(ExchangeModel, ex_id)
    
    def get_code_by_id(self, ex_id:int) -> Optional[str]:
        return self._db.execute(
            select(ExchangeModel.code).where(ExchangeModel.id==ex_id)
        ).scalar_one_or_none()