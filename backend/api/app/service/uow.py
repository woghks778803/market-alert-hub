from sqlalchemy.orm import Session
from app.repository.protocol.user_repo import UserRepo    
from app.repository.sql.user_repo import SqlUserRepo       
from app.repository.protocol.alert_repo import AlertRepo    
from app.repository.sql.alert_repo import SqlAlertRepo       

class UnitOfWork:
    """한 요청 내에서 여러 레포가 같은 DB 세션을 공유하도록 보장."""
    def __init__(self, db: Session) -> None:
        self.db = db
        # 여기에 자주 쓰는 Repo들을 미리 구성해둡니다. 직접 수정은 x(_)
        self._users = None
        self._alerts = None

    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        if exc: self.rollback()
        return False

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    # --- Lazy repositories (처음 호출 시 생성 후 캐시) ---
    @property
    def users(self) -> UserRepo:
        if self._users is None:
            self._users = SqlUserRepo(self.db)
        return self._users
    
    @property
    def alerts(self) -> AlertRepo:
        if self._alerts is None:
            self._alerts = SqlAlertRepo(self.db)
        return self._alerts

