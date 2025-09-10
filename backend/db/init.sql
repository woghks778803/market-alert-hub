CREATE SCHEMA IF NOT EXISTS market_alert_hub 
  DEFAULT CHARACTER SET utf8mb4 
  COLLATE utf8mb4_0900_ai_ci;
USE market_alert_hub;

-- ---------------------
-- Users / Auth
-- ---------------------
CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '사용자 PK',
  email VARCHAR(255) NOT NULL UNIQUE COMMENT '로그인용 이메일 (UNIQUE)',
  password_hash VARCHAR(255) COMMENT '비밀번호 해시(bcrypt/argon2)',
  nickname VARCHAR(100) COMMENT '사용자 표시 이름',
  status ENUM('active','suspended','deleted') NOT NULL DEFAULT 'active' COMMENT '계정 상태',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '계정 생성 시각',
  last_login_at DATETIME(6) COMMENT '마지막 로그인 시각'
) ENGINE=InnoDB COMMENT='서비스 회원 기본 정보';

CREATE TABLE user_identities (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '소셜 계정 매핑 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  provider ENUM('google','github','kakao','naver') COMMENT 'OAuth 제공자',
  provider_user_id VARCHAR(255) NOT NULL COMMENT '제공자 측 사용자 ID',
  access_token TEXT COMMENT '액세스 토큰',
  refresh_token TEXT COMMENT '리프레시 토큰',
  expires_at DATETIME(6) COMMENT '토큰 만료 시각',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '등록 시각',
  UNIQUE KEY uk_provider_user (provider, provider_user_id),
  CONSTRAINT fk_ui_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='소셜 로그인 계정 정보';

CREATE TABLE sessions (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '세션 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  token_hash CHAR(64) NOT NULL UNIQUE COMMENT '세션 토큰 해시',
  user_agent VARCHAR(255) COMMENT '사용자 에이전트',
  ip_addr VARCHAR(45) COMMENT '로그인 IP',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '세션 생성 시각',
  expires_at DATETIME(6) NOT NULL COMMENT '세션 만료 시각',
  revoked_at DATETIME(6) COMMENT '세션 강제 종료 시각',
  INDEX idx_sessions_user (user_id),
  INDEX idx_sessions_exp (expires_at),
  CONSTRAINT fk_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='로그인 세션 및 토큰 관리';

CREATE TABLE password_resets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '비밀번호 재설정 요청 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  token_hash CHAR(64) NOT NULL UNIQUE COMMENT '비밀번호 재설정 토큰 해시',
  expires_at DATETIME(6) NOT NULL COMMENT '토큰 만료 시각',
  used_at DATETIME(6) COMMENT '토큰 사용 시각',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
  CONSTRAINT fk_pr_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='비밀번호 재설정 토큰 관리';

-- ---------------------
-- Markets
-- ---------------------
CREATE TABLE exchanges (
  id INT PRIMARY KEY AUTO_INCREMENT COMMENT '거래소 PK',
  code VARCHAR(32) NOT NULL UNIQUE COMMENT '거래소 코드 (예: BINANCE, UPBIT)',
  name VARCHAR(100) NOT NULL COMMENT '거래소 이름',
  country VARCHAR(64) COMMENT '소속 국가',
  timezone VARCHAR(64) NOT NULL DEFAULT 'UTC' COMMENT '거래소 기준 타임존',
  base_url VARCHAR(255) COMMENT '거래소 API Base URL',
  status ENUM('active','inactive') NOT NULL DEFAULT 'active' COMMENT '거래소 상태',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '등록 시각'
) ENGINE=InnoDB COMMENT='거래소 메타 정보';

CREATE TABLE instruments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '종목 PK',
  symbol VARCHAR(64) NOT NULL UNIQUE COMMENT '심볼 (예: BTCUSDT)',
  base_asset VARCHAR(32) NOT NULL COMMENT '기초 자산 (예: BTC)',
  quote_asset VARCHAR(32) NOT NULL COMMENT '상대 자산 (예: USDT)',
  asset_type ENUM('CRYPTO','FX','STOCK','FUTURE') NOT NULL DEFAULT 'CRYPTO' COMMENT '자산 유형',
  tick_size DECIMAL(20,10) NOT NULL DEFAULT 0.00000001 COMMENT '호가 단위',
  lot_size  DECIMAL(20,10) NOT NULL DEFAULT 0.00000001 COMMENT '거래 단위',
  status ENUM('active','inactive') NOT NULL DEFAULT 'active' COMMENT '종목 상태',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '등록 시각'
) ENGINE=InnoDB COMMENT='거래 가능한 종목 정보';

CREATE TABLE exchange_instruments (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '거래소별 종목 매핑 PK',
  exchange_id INT NOT NULL COMMENT 'FK → exchanges.id',
  instrument_id BIGINT NOT NULL COMMENT 'FK → instruments.id',
  exchange_symbol VARCHAR(64) NOT NULL COMMENT '거래소 내 표기 심볼',
  price_precision INT NOT NULL DEFAULT 8 COMMENT '가격 소수점 정밀도',
  qty_precision   INT NOT NULL DEFAULT 8 COMMENT '수량 소수점 정밀도',
  min_notional DECIMAL(20,10) COMMENT '최소 거래 금액',
  active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '활성 여부',
  UNIQUE KEY uk_ex_inst (exchange_id, instrument_id),
  INDEX idx_ex_sym (exchange_id, exchange_symbol),
  CONSTRAINT fk_ei_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
  CONSTRAINT fk_ei_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id)
) ENGINE=InnoDB COMMENT='거래소별 종목 심볼 매핑';

-- ---------------------
-- Prices
-- ---------------------
CREATE TABLE prices_latest (
  exchange_id INT NOT NULL COMMENT 'FK → exchanges.id',
  instrument_id BIGINT NOT NULL COMMENT 'FK → instruments.id',
  last_price DECIMAL(32,16) NOT NULL COMMENT '최근 가격',
  volume_24h DECIMAL(32,16) COMMENT '24시간 거래량',
  high_24h DECIMAL(32,16) COMMENT '24시간 최고가',
  low_24h  DECIMAL(32,16) COMMENT '24시간 최저가',
  ts DATETIME(6) NOT NULL COMMENT '수집 시각 (UTC)',
  PRIMARY KEY (exchange_id, instrument_id),
  INDEX idx_prices_ts (ts),
  CONSTRAINT fk_pl_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
  CONSTRAINT fk_pl_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id)
) ENGINE=InnoDB COMMENT='거래소×종목 최신 시세';

CREATE TABLE price_snapshots_1m (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '1분봉 PK',
  exchange_id INT NOT NULL COMMENT 'FK → exchanges.id',
  instrument_id BIGINT NOT NULL COMMENT 'FK → instruments.id',
  bucket_minute DATETIME NOT NULL COMMENT '분 단위 버킷 (YYYY-MM-DD HH:MM:00)',
  open_price DECIMAL(32,16) COMMENT '시가',
  high_price DECIMAL(32,16) COMMENT '고가',
  low_price  DECIMAL(32,16) COMMENT '저가',
  close_price DECIMAL(32,16) COMMENT '종가',
  volume DECIMAL(32,16) COMMENT '거래량',
  UNIQUE KEY uk_ohlcv_1m (exchange_id, instrument_id, bucket_minute),
  INDEX idx_bucket (bucket_minute),
  INDEX idx_inst_bucket (instrument_id, bucket_minute),
  CONSTRAINT fk_ps_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
  CONSTRAINT fk_ps_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id)
) ENGINE=InnoDB COMMENT='거래소×종목 1분 OHLCV 스냅샷';

-- ---------------------
-- Alerts
-- ---------------------
CREATE TABLE alerts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '알림 규칙 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  name VARCHAR(100) NOT NULL COMMENT '알림 이름',
  status ENUM('active','paused','archived') NOT NULL DEFAULT 'active' COMMENT '알림 상태',
  type ENUM('price_above','price_below','pct_change_window','cross_exchange_spread','volume_above','moving_avg_cross') NOT NULL COMMENT '알림 유형',
  scope ENUM('single_exchange','cross_exchange') NOT NULL DEFAULT 'single_exchange' COMMENT '단일/교차 거래소 범위',
  exchange_id INT NULL COMMENT '대상 거래소 (scope=single_exchange)',
  instrument_id BIGINT NULL COMMENT '대상 종목',
  params JSON NOT NULL COMMENT '알림 조건 파라미터(JSON)',
  throttle_seconds INT NOT NULL DEFAULT 300 COMMENT '중복 발송 최소 간격(초)',
  valid_from DATETIME(6) NULL COMMENT '유효 시작 시각',
  valid_to   DATETIME(6) NULL COMMENT '유효 종료 시각',
  timezone  VARCHAR(64) NOT NULL DEFAULT 'UTC' COMMENT '조건 해석 기준 타임존',
  last_fired_at DATETIME(6) NULL COMMENT '마지막 발동 시각',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '갱신 시각',
  UNIQUE KEY uk_user_alert_name (user_id, name),
  INDEX idx_alert_user (user_id),
  INDEX idx_alert_status (status),
  INDEX idx_alert_type (type),
  INDEX idx_alert_inst (instrument_id),
  INDEX idx_alert_ex (exchange_id),
  CONSTRAINT fk_alert_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_alert_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
  CONSTRAINT fk_alert_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id)
) ENGINE=InnoDB COMMENT='사용자 알림 규칙 정의';

CREATE TABLE user_channels (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '발송 채널 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  channel_type ENUM('email','webhook','telegram','slack') NOT NULL COMMENT '채널 유형',
  address VARCHAR(255) COMMENT '주소 (email/webhook/chat_id 등)',
  config JSON COMMENT '채널별 추가 설정(JSON)',
  verified_at DATETIME(6) COMMENT '검증 완료 시각',
  is_default BOOLEAN NOT NULL DEFAULT FALSE COMMENT '기본 채널 여부',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '등록 시각',
  INDEX idx_uc_user (user_id),
  INDEX idx_uc_type (channel_type),
  CONSTRAINT fk_uc_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='사용자 발송 채널';

CREATE TABLE alert_channel_targets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '알림-채널 매핑 PK',
  alert_id BIGINT NOT NULL COMMENT 'FK → alerts.id',
  user_channel_id BIGINT NOT NULL COMMENT 'FK → user_channels.id',
  is_primary BOOLEAN NOT NULL DEFAULT FALSE COMMENT '주 채널 여부',
  UNIQUE KEY uk_alert_channel (alert_id, user_channel_id),
  INDEX idx_act_alert (alert_id),
  CONSTRAINT fk_act_alert FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
  CONSTRAINT fk_act_uc FOREIGN KEY (user_channel_id) REFERENCES user_channels(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='알림 규칙과 발송 채널 매핑';

CREATE TABLE alert_events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '알림 이벤트 PK',
  alert_id BIGINT NOT NULL COMMENT 'FK → alerts.id',
  detected_at DATETIME(6) NOT NULL COMMENT '조건 충족 시각',
  exchange_id INT NULL COMMENT '조건 발생 거래소',
  instrument_id BIGINT NULL COMMENT '조건 발생 종목',
  trigger_value DECIMAL(32,16) COMMENT '트리거 값',
  context JSON COMMENT '발동 당시 시세/context',
  dedup_key VARCHAR(64) COMMENT '중복 방지 키',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
  INDEX idx_ae_alert_time (alert_id, detected_at DESC),
  UNIQUE KEY uk_ae_dedup (dedup_key),
  CONSTRAINT fk_ae_alert FOREIGN KEY (alert_id) REFERENCES alerts(id) ON DELETE CASCADE,
  CONSTRAINT fk_ae_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id),
  CONSTRAINT fk_ae_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id)
) ENGINE=InnoDB COMMENT='알림 발동 이벤트 로그';

CREATE TABLE deliveries (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '발송 이력 PK',
  alert_event_id BIGINT NOT NULL COMMENT 'FK → alert_events.id',
  user_channel_id BIGINT NOT NULL COMMENT 'FK → user_channels.id',
  status ENUM('queued','sent','failed') NOT NULL DEFAULT 'queued' COMMENT '발송 상태',
  sent_at DATETIME(6) COMMENT '발송 시각',
  response_code INT COMMENT '응답 코드',
  response_body TEXT COMMENT '응답 본문',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '생성 시각',
  INDEX idx_del_event (alert_event_id),
  INDEX idx_del_channel (user_channel_id),
  INDEX idx_del_status (status),
  CONSTRAINT fk_del_event FOREIGN KEY (alert_event_id) REFERENCES alert_events(id) ON DELETE CASCADE,
  CONSTRAINT fk_del_uc FOREIGN KEY (user_channel_id) REFERENCES user_channels(id)
) ENGINE=InnoDB COMMENT='알림 발송 이력';

-- ---------------------
-- Watchlist
-- ---------------------
CREATE TABLE watchlist_items (
  id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '관심 종목 PK',
  user_id BIGINT NOT NULL COMMENT 'FK → users.id',
  instrument_id BIGINT NULL COMMENT 'FK → instruments.id',
  exchange_id INT NULL COMMENT 'FK → exchanges.id',
  note VARCHAR(255) COMMENT '메모',
  sort_order INT DEFAULT 0 COMMENT '정렬 순서',
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '등록 시각',
  INDEX idx_wl_user (user_id),
  INDEX idx_wl_inst (instrument_id),
  INDEX idx_wl_ex (exchange_id),
  CONSTRAINT fk_wl_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_wl_inst FOREIGN KEY (instrument_id) REFERENCES instruments(id),
  CONSTRAINT fk_wl_ex FOREIGN KEY (exchange_id) REFERENCES exchanges(id)
) ENGINE=InnoDB COMMENT='사용자 관심 종목 목록';
