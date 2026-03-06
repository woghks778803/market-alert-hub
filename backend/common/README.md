# Common Layer (Shared Application Core)

여러 서비스(api, worker, collector, scheduler, dispatcher)가 공통으로 사용하는 애플리케이션 계층입니다. 도메인 규칙, 인프라 어댑터, 서비스/런타임 부트스트랩을 한 곳에 두어 중복을 줄이고 일관된 동작을 보장합니다.

## Purpose
- 도메인 로직과 인프라 의존성을 모듈화해 모든 서비스가 동일한 규칙과 구현을 재사용.
- 각 실행 서비스는 자신만의 엔트리포인트를 가지되, 공통 컨텍스트와 서비스 팩토리를 이 레이어에서 받아 사용.

## Directory Structure
- `core/`
  - 공통 상수, DTO, 로깅/유틸 등 **서비스 무관한 기초 타입**을 제공.
- `domain/`
  - 도메인 모델과 포트(인터페이스), 에러, 유즈케이스 규칙을 정의.
  - auth, user, channel, market, outbox, watchlist 등 **비즈니스 규칙의 집합**.
- `service/`
  - 도메인 포트를 구현하는 **애플리케이션 서비스 계층**.
  - `service/factory.py`가 UnitOfWork, crypto/email/redis/oauth/exchange 등 어댑터를 주입해 서비스 인스턴스를 구성.
- `infra/`
  - 데이터베이스, 외부 시스템 어댑터 구현.
  - `infra/db`: SQLAlchemy 모델, 엔진/세션, UnitOfWork, Alembic 템플릿.
  - `infra/external`: Redis 클라이언트, Kakao OAuth, AWS SES, JWT/HMAC/암호화, Upbit WS/REST 등 외부 포트 구현.
- `runtime/`
  - 실행 환경 부트스트랩과 설정.
  - `settings.py`: Pydantic BaseSettings로 환경변수 로딩.
  - `bootstrap.py`: Providers와 ConfigBag을 조립해 `ServiceFactory`와 각 컨텍스트(ApiContext, WorkerContext, DispatcherContext, SchedulerContext, CollectorContext)를 생성·캐시.
  - `app_context.py`: 컨텍스트 데이터클래스 정의.
  - `ports.py`, `aio/`, `sync/`: 런타임 보조 포트/헬퍼.
- `templates/`
  - 이메일 HTML 템플릿 등 **크로스 서비스 자산**을 보관 (예: 인증 메일, 비밀번호 재설정, 알림).
- `script/`
  - 보조 스크립트(테스트, 브랜치 정리 등).

## 층간 상호작용 (전형적 흐름)
1) 각 서비스(api/worker/collector/dispatcher/scheduler)가 자신의 엔트리포인트에서 `runtime.bootstrap`의 `create_*_context()`를 호출.
2) 부트스트랩이 환경설정(`settings`)을 읽고, DB/Redis/JWT/암호화/외부 API 어댑터를 Provider로 생성.
3) Provider들이 `service.factory.ServiceFactory`에 주입되어 도메인 서비스(유저, 인증, 알림, 시장, 워치리스트 등)를 제공.
4) 라우터나 워커 루프는 `ServiceFactory`를 통해 도메인 로직을 호출하고, UnitOfWork가 트랜잭션을 관리.
5) 외부 연동은 `infra/external` 어댑터를 통해 수행되며, 공통 설정과 비밀은 `settings`/Providers가 해결.

## Related Services
- **api**: `create_api_context()`로 `ApiContext(config, svcs)`를 받아 HTTP 의존성 주입(`deps.get_services`)에 사용.
- **worker**: `create_worker_context()`로 워커 설정·Redis·ServiceFactory를 얻어 outbox 처리, 이메일/알림 전송 등 실행.
- **dispatcher**: `create_dispatcher_context()`를 통해 Redis와 서비스 팩토리로 알림 디스패치 루프 구성.
- **scheduler**: `create_scheduler_context()`로 스케줄 설정·Redis·서비스 팩토리를 받아 주기 작업을 트리거.
- **collector**: `create_collector_context()`로 Upbit WS/REST, Redis active catalog, async Redis 등을 묶어 시세 수집 스트림을 실행.

이 문서는 공통 레이어의 아키텍처와 책임을 이해하기 위한 것이며, 구체적인 비즈니스 로직이나 설정 값은 각 하위 모듈과 서비스 엔트리포인트에서 확인할 수 있습니다.
