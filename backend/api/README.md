# API Service (FastAPI)

코드 기준으로 API 서비스의 구조와 책임을 요약합니다.

## 1. 엔트리포인트 (`app/main.py`)
- `create_app()`에서 FastAPI 인스턴스를 생성하고:
  - 배포 환경에 따라 로깅 레벨 설정
  - Sentry 초기화 및 service 태그 설정
  - 미들웨어 등록(RequestId, CORS)
  - 공통 예외 핸들러 등록
  - 라우터 트리(`api`) 포함
  - Swagger/OpenAPI 스키마에 태그 그룹 적용
- 모듈 하단에서 `app = create_app()`로 실제 앱 인스턴스를 노출.

## 2. Directory Structure
- `api/` : HTTP 레이어
  - `router/` : 퍼블릭(`/api`)·어드민(`/admin-api`) 라우터 모듈
  - `deps.py` : DI 정의(서비스/토큰/현재 사용자/관리자 체크)
  - `middleware.py` : 요청 ID 부여·로깅
  - `exception_handlers.py` : 단일 예외 처리 → Envelope 오류 응답, Sentry 연동
  - `common/envelope.py` : 공통 응답 래퍼(success/error/meta)
  - `openapi/` : 응답 스펙 조각, 결합 유틸
  - `schema/` : Pydantic 요청/응답 스키마 (Auth, User, Market 등)
- `ws/` : WS 레이어
  - `consumers/` : Redis stream consumer (background loop)
  - `handlers.py` : client message 처리 (subscribe/unsubscribe)
  - `hub.py` : connection + subscription 관리 (in-memory)
  - `protocols.py` : websocket message schema / validation
  - `auth.py` : websocket 인증 처리
  - `throttle.py` : rate limit / 보호 로직 (optional)
- `main.py` : 앱 생성과 미들웨어/라우터 부착.

## 3. routing
- 퍼블릭 루트: `router/public/__init__.py` → prefix `/api`
  - 인증, 사용자, 마켓 데이터, 알림 채널 등 도메인별 API 라우터로 구성.
- 어드민 루트: `router/admin/__init__.py` → prefix `/admin-api`
  - 공개: admin 로그인
  - 보호: Users 등 (Security `require_admin` 의존성 적용)
- 라우터는 `app/api/router/__init__.py`에서 하나의 `api`로 합쳐져 `main.py`에 포함.

## 4. 의존성 주입
- `deps.get_app_context()`가 `backend/common/app/runtime/bootstrap.create_api_context()`를 1회 생성·캐시.
- `get_services()`가 `ServiceFactory` 인스턴스를 주입해 도메인 서비스에 접근.
- 인증 관련:
  - `get_current_token()`이 Bearer 토큰을 추출/검증.
  - `get_current_user()`가 JWT 디코드 후 `CurrentUser`를 반환, 만료·페이로드 오류는 `AuthError`로 처리.
  - `require_admin`이 관리자 역할을 검사.
- `get_request_meta()`가 request_id와 타임스탬프를 내려 응답 메타에 사용.

## 5. 미들웨어
- `RequestIdMiddleware`: 요청마다 UUID 또는 전달된 `x-request-id`를 state/응답 헤더에 설정하고 처리 시간 로깅, 트레이스 ID 컨텍스트에 기록.
- `CORSMiddleware`: `main.py`에서 도메인 화이트리스트 기반으로 허용.
*(FastAPI 기본 ExceptionMiddleware는 기본 포함)*

## 6. 인증 흐름
- 클라이언트는 Authorization: Bearer JWT로 요청.
- 전역 디펜던시가 JWT 서명/만료/클레임(sub, role, ev 등)을 검증하여 `CurrentUser`를 해석.
- 라우트별로 `Security(get_current_user)` 또는 `Security(require_admin)`로 보호.
- 리프레시 토큰은 쿠키(`refresh_token`)로 전달되며, `/auth/reissue` 등이 액세스 토큰 재발급을 수행.

## 7. 외부 의존성 / 런타임
- 런타임 부팅은 `backend/common/app/runtime/`의 프로바이더를 사용:
  - Database(Session/UnitOfWork) 프로바이더
  - Redis 클라이언트 프로바이더
  - JWT 서명/검증
  - 데이터 암호화 유틸
  - 외부 서비스: Kakao OAuth, AWS SES
  - 거래소 클라이언트: Upbit WS/REST
- 실제 설정 값은 공용 런타임에서 불러오며, API 서비스는 `ServiceFactory`를 통해 사용.

## 8. 응답 패턴
- 모든 주요 핸들러는 `Envelope` 포맷(success/data/error/meta)으로 응답.
- 예외 발생 시 `unified_exception_handler`가 오류를 표준화하고 Sentry·로그에 기록한 뒤 동일 Envelope 형식으로 반환.

이 문서는 아키텍처와 책임에 초점을 둡니다. 세부 구현(개별 서비스 메서드, 세부 설정 값)은 코드와 공용 런타임을 참고하세요.
