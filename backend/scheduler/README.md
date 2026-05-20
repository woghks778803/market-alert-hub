# Scheduler Service

## Purpose
- 주기적으로 도메인 작업을 트리거하는 스케줄러. 카탈로그 동기화, 스냅샷 적재 등 후속 파이프라인 처리를 위한 Outbox 이벤트를 생성한다

## Responsibilities
- 설정된 인터벌마다 작업 슬롯을 계산하고, 중복 없이 아웃박스를 기록.
- 심볼/거래소 동기화, 스냅샷 적재(여러 주기) 등 배치 트리거 정의.
- 재시작 시 슬롯 기반으로 자동 복구되도록 체크포인트/재시작 정책을 적용.
- 후속 처리(dispatcher/worker)가 소비할 Outbox 이벤트를 기록한다.

## Entrypoint
- `app/main.py`: 로깅·Sentry 초기화 후 `build_runtime()` → `run(runtime)` 실행.
- `app/wiring.py`: `create_scheduler_context()`로 공용 컨텍스트를 불러와 체크포인트 스토어, 재시작 정책, 실행 스펙(스레드 작업)을 조립.
- `app/run.py`: `stop_event`를 관리하며 supervised 스레드를 실행/정리.
- 실행 작업: `_build_specs`가 단일 `scheduler` 작업을 만들어 `run_scheduler_loop`(1초 tick 루프)을 실행.

## Dependencies
- 공용 런타임(`backend/common/app/runtime/bootstrap.create_scheduler_context`): ServiceFactory(도메인 서비스), Redis 클라이언트, 설정(ConfigBag) 주입.
- 체크포인트 스토어: 기본 메모리, 설정 시 파일 사용.
- Sentry/로깅: 서비스 레벨 로깅 및 오류 리포팅.

## Data Flow
1) `run_scheduler_loop`가 1초 단위 tick을 돌며 `IntervalTask` 리스트를 순회.
2) 각 `IntervalTask`는 slot(초/interval) 변화 시 한 번만 실행되어 핸들러를 호출.
3) 핸들러(`handlers.py`)가 `ctx.svcs.outboxs.create_outbox`를 통해 Outbox 레코드를 생성(이벤트 유형: SYNC_EXCHANGES, SYNC_SYMBOLS, PERSIST_SNAPSHOTS 등).
4) Outbox는 DB/Redis를 통해 Dispatcher/Worker가 후속 처리(수집, 알림 트리거, 스냅샷 적재 등)를 이어받는다.
5) 예외는 로깅되고, supervisor가 재시작 정책(백오프/재시도)으로 스레드를 복구.

## Related Services
- **dispatcher**: Scheduler가 적재한 Outbox를 폴링해 실제 작업(동기화, 알림 트리거 등)을 분배.
- **worker**: Dispatcher가 큐잉한 작업을 실행하거나 직접 Outbox를 소비해 이메일/알림/스냅샷 처리를 수행.
- **collector**: SYNC_EXCHANGES/SYNC_SYMBOLS로 갱신된 카탈로그를 기반으로 WS 구독 대상을 최신 상태로 유지.
- **api**: 필요 시 스케줄 상태/카탈로그 데이터를 조회하거나 관리 기능으로 확장 가능.
