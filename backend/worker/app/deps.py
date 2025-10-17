from app.service.factory import ServiceFactory
from app.infra.db.uow import UnitOfWork
from app.infra.db.engine import SessionLocal
from app.runtime.bootstrap import create_service_factory


def get_services() -> ServiceFactory:
    uow_provider = lambda: UnitOfWork(SessionLocal, owns_session=True)
    return create_service_factory(uow_provider)
