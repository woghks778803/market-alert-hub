from app.runtime.bootstrap import get_core_services, get_core_worker_config_bag
from app.service.factory import ServiceFactory

worker_config = get_core_worker_config_bag()


def get_services() -> ServiceFactory:
    svcs = get_core_services()
    return svcs
