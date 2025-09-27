from sqlalchemy.orm import Session as DbSession

from app.repository.protocol.user_repo import UserRepo    
from app.repository.sql.user_repo import SqlUserRepo       
from app.repository.protocol.alert_repo import AlertRepo    
from app.repository.sql.alert_repo import SqlAlertRepo    
from app.repository.protocol.session_repo import SessionRepo    
from app.repository.sql.session_repo import SqlSessionRepo  
from app.repository.protocol.market_repo import MarketRepo    
from app.repository.sql.market_repo import SqlMarketRepo    
from app.repository.protocol.watchlist_repo import WatchlistRepo    
from app.repository.sql.watchlist_repo import SqlWatchlistRepo  

class UnitOfWork:
    def __init__(self, db: DbSession, owns_session: bool = True) -> None:
        self.db = db
        self._users = None
        self._sessions = None
        self._alerts = None
        self._markets = None
        self._watchlists = None
        self._done = False
        self._owns = owns_session

    def __enter__(self): return self
    def __exit__(self, exc_type, *_):
        if not self.db: return False
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

    def rollback(self) -> None:
        if not self._done:
            self.db.rollback()
            self._done = True

    # --- Lazy repositories (처음 호출 시 생성 후 캐시) ---
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

