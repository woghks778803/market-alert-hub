from sqlalchemy.orm import Session
from app.repository import SqlUserRepo  # 필요에 따라 다른 Repo도 추가

class UnitOfWork:
    """한 요청 내에서 여러 레포가 같은 DB 세션을 공유하도록 보장."""
    def __init__(self, db: Session) -> None:
        self.db = db
        # 여기에 자주 쓰는 Repo들을 미리 구성해둡니다.
        self.users = SqlUserRepo(db)
        # self.alerts = SqlAlertRepo(db)
        # self.channels = SqlChannelRepo(db)

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()
