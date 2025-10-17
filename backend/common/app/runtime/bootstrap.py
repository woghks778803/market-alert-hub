from .settings import settings
from app.infra.db.engine import SessionLocal  
from app.infra.external.email.ses_client import SesEmailClient
from app.infra.external.email.jinja_renderer import JinjaEmailRenderer
from app.infra.db.uow import UnitOfWork
from app.service.factory import ServiceFactory
from typing import Callable

class Providers:
    @staticmethod
    def email_client_provider() -> Callable[[], SesEmailClient]:
        return lambda: SesEmailClient()

    @staticmethod
    def email_renderer_provider() -> Callable[[], JinjaEmailRenderer]:
        return lambda: JinjaEmailRenderer()

    @staticmethod
    def create_uow_from_session(db_session) -> Callable[[], UnitOfWork]:
        return lambda: UnitOfWork(db_session, owns_session=True)

providers = Providers()

def create_service_factory(uow_provider: Callable[[], UnitOfWork]) -> ServiceFactory:
    return ServiceFactory(
        uow=uow_provider,  
        email_client=providers.email_client_provider(),    
        email_renderer=providers.email_renderer_provider(),
        jwt_secret=settings.JWT_SECRET,
        token_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
