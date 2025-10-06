from sqlalchemy.orm import Session as DbSession

from app.infra.db.repository.protocol.user_repo import UserRepo    
from app.infra.db.repository.sql.user_repo import SqlUserRepo       
from app.infra.db.repository.protocol.alert_repo import AlertRepo    
from app.infra.db.repository.sql.alert_repo import SqlAlertRepo    
from app.infra.db.repository.protocol.session_repo import SessionRepo    
from app.infra.db.repository.sql.session_repo import SqlSessionRepo  
from app.infra.db.repository.protocol.market_repo import MarketRepo    
from app.infra.db.repository.sql.market_repo import SqlMarketRepo    
from app.infra.db.repository.protocol.watchlist_repo import WatchlistRepo    
from app.infra.db.repository.sql.watchlist_repo import SqlWatchlistRepo  
from app.infra.db.repository.protocol.channel_repo import ChannelRepo    
from app.infra.db.repository.sql.channel_repo import SqlChannelRepo  
from app.infra.db.repository.protocol.provider_repo import ProviderRepo    
from app.infra.db.repository.sql.provider_repo import SqlProviderRepo  

class UnitOfWork:
    def __init__(self, db: DbSession, owns_session: bool = True) -> None:
        self.db = db
        self._users = None
        self._sessions = None
        self._alerts = None
        self._markets = None
        self._watchlists = None
        self._channels = None
        self._providers = None
        
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

    @property
    def channels(self) -> ChannelRepo:
        if self._channels is None:
            self._channels = SqlChannelRepo(self.db)
        return self._channels
    
    @property
    def providers(self) -> ProviderRepo:
        if self._providers is None:
            self._providers = SqlProviderRepo(self.db)
        return self._providers
