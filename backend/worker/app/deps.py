from app.service.factory import ServiceFactory
from app.infra.db.uow import UnitOfWork
from app.infra.db.engine import SessionLocal


def get_services() -> ServiceFactory:
    # worker는 요청 스코프가 없으므로 직접 세션팩토리 사용
    return ServiceFactory(lambda: UnitOfWork(SessionLocal))