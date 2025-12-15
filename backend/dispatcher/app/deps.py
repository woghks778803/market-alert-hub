from app.runtime.bootstrap import get_core_services
from app.service.factory import ServiceFactory

def get_services()-> ServiceFactory:
    svcs = get_core_services()
    return svcs