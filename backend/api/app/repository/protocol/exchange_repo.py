from typing import Protocol
from app.infra.db.model import Exchange


class ExchangeRepo(Protocol):
    def get_by_id(self, ex_id:int) -> Exchange | None: ...
    def get_code_by_id(self, ex_id:int) -> str | None: ...