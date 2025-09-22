from app.service.uow import UnitOfWork
from app.api.schema.alert import AlertCreate

class AlertService:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def create(self, user_id: int, data: AlertCreate):
        with self.uow as u:
            a = u.alerts.add(user_id, **data.model_dump())  # 타입 안전 + 결합 낮음
            u.commit()
            return a
        
    def create(self, user_id: int, data):
        with self.uow as u:
            a = u.alerts.add(user_id, data)
            u.commit()
            return a

    def list(self, user_id: int):
        with self.uow as u:
            return u.alerts.list_by_user(user_id)

    def delete(self, user_id: int, alert_id: int):
        with self.uow as u:
            u.alerts.delete(user_id, alert_id)
            u.commit()
