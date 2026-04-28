from typing import Union
from sqlalchemy.orm import Session as DbSession, sessionmaker
from sqlalchemy.exc import IntegrityError
from app.domain.shared.uow import UnitOfWork as UnitOfWorkPort
from app.infra.db.utils import is_mysql_duplicate_key

from app.infra.db.repository.protocol.user_repo import UserRepo
from app.infra.db.repository.protocol.session_repo import SessionRepo
from app.infra.db.repository.protocol.alert_repo import AlertRepo
from app.infra.db.repository.protocol.market_repo import MarketRepo
from app.infra.db.repository.protocol.watchlist_repo import WatchlistRepo
from app.infra.db.repository.protocol.channel_repo import ChannelRepo
from app.infra.db.repository.protocol.outbox_repo import OutboxRepo
from app.infra.db.repository.protocol.support_repo import SupportRepo
from app.infra.db.repository.protocol.news_repo import NewsRepo

from app.infra.db.repository.sql.user_repo import SqlUserRepo
from app.infra.db.repository.sql.session_repo import SqlSessionRepo
from app.infra.db.repository.sql.alert_repo import SqlAlertRepo
from app.infra.db.repository.sql.market_repo import SqlMarketRepo
from app.infra.db.repository.sql.watchlist_repo import SqlWatchlistRepo
from app.infra.db.repository.sql.channel_repo import SqlChannelRepo
from app.infra.db.repository.sql.outbox_repo import SqlOutboxRepo
from app.infra.db.repository.sql.support_repo import SqlSupportRepo
from app.infra.db.repository.sql.news_repo import SqlNewsRepo

class UnitOfWork(UnitOfWorkPort):
    def __init__(
        self, 
        db: Union[DbSession, sessionmaker[DbSession]], 
        owns_session: bool = True
    ) -> None:
        self.db: DbSession = db() if callable(db) else db
        self._users = None
        self._sessions = None
        self._alerts = None
        self._markets = None
        self._watchlists = None
        self._channels = None
        self._providers = None
        self._outboxs = None
        self._supports = None
        self._news = None

        self._done = False
        self._owns = owns_session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, *_):
        if not self.db:
            return False
            
        try:
            if exc_type and not self._done:
                self.db.rollback()
        finally:
            if self._owns:
                self.db.close()
        return False

    def commit(self) -> None:
        if not self._done:
            self.db.commit()
            self._done = True

    def commit_outbox_idempotent(self) -> None:
        if self._done:
            return

        try:
            self.db.commit()
            self._done = True
        except IntegrityError as e:

            if is_mysql_duplicate_key(e):
                # 이미 같은 fingerprint가 존재 → 정상 처리
                self.db.rollback()
                self._done = True
                return
            raise

    def rollback(self) -> None:
        if not self._done:
            self.db.rollback()
            self._done = True

    def flush(self) -> None:
        if self._done:
            return
        self.db.flush()

    # ---- lazy repositories (서비스 시그니처는 그대로: uow.users ...) ----
    @property
    def users(self) -> UserRepo:
        if self._users is None:
            self._users = SqlUserRepo(self.db)
        return self._users

    @property
    def sessions(self) -> SessionRepo:
        if self._sessions is None:
            self._sessions = SqlSessionRepo(self.db)
        return self._sessions

    @property
    def alerts(self) -> AlertRepo:
        if self._alerts is None:
            self._alerts = SqlAlertRepo(self.db)
        return self._alerts

    @property
    def markets(self) -> MarketRepo:
        if self._markets is None:
            self._markets = SqlMarketRepo(self.db)
        return self._markets

    @property
    def watchlists(self) -> WatchlistRepo:
        if self._watchlists is None:
            self._watchlists = SqlWatchlistRepo(self.db)
        return self._watchlists

    @property
    def channels(self) -> ChannelRepo:
        if self._channels is None:
            self._channels = SqlChannelRepo(self.db)
        return self._channels

    @property
    def outboxs(self) -> OutboxRepo:
        if self._outboxs is None:
            self._outboxs = SqlOutboxRepo(self.db)
        return self._outboxs

    @property
    def supports(self) -> SupportRepo:
        if self._supports is None:
            self._supports = SqlSupportRepo(self.db)
        return self._supports

    @property
    def newses(self) -> NewsRepo:
        if self._news is None:
            self._news = SqlNewsRepo(self.db)
        return self._news
