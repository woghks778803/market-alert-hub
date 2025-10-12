from typing import List, Optional
from sqlalchemy.orm import Session as DbSession
from app.infra.db.model import AlertModel
from ..protocol.alert_repo import AlertRepo

class SqlAlertRepo(AlertRepo):
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, user_id:int, *, exchange_id:int, symbol:str, target_price:float, direction:str) -> AlertModel:
        a = AlertModel(user_id=user_id, exchange_id=exchange_id, symbol=symbol,
                target_price=target_price, direction=direction, status="active")
        self._db.add(a)
        self._db.flush()      # id 채우기
        self._db.refresh(a)
        return a

    def list_by_user(self, user_id: int) -> List[AlertModel]:
        return list(self._db.query(AlertModel).filter(AlertModel.user_id == user_id).all())

    def get(self, user_id: int, alert_id: int) -> Optional[AlertModel]:
        return (
            self._db.query(AlertModel)
            .filter(AlertModel.user_id == user_id, AlertModel.id == alert_id)
            .first()
        )

    def delete(self, user_id: int, alert_id: int) -> None:
        a = self.get(user_id, alert_id)
        if a:
            self._db.delete(a)
