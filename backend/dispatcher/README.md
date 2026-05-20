# Dispatcher Service

## Purpose
- Outbox에 적재된 예약/스케줄 이벤트를 폴링해 작업 큐(RQ)로 전달하는 라우팅 전담 서비스.

## Responsibilities
- DB의 Outbox pending 항목을 주기적으로 조회.
- 이벤트를 RQ Queue(`outbox`)에 enqueue하여 워커가 소비하도록 전달.
- 폴링 간격과 배치 크기(poll_limit/idle_sleep)를 설정 기반으로 제어.
- 장애 시 로깅·Sentry 보고, 신호(SIGTERM/SIGINT)로 안전 종료.

## Entrypoint
- `app/main.py` → `app/run.py`.
- `app/wiring.py`에서 공용 컨텍스트(`create_dispatcher_context`)를 통해 ServiceFactory, DispatcherConfigBag, Redis 연결, RQ Queue를 조립.

## Dependencies
- 공용 런타임: `backend/common/app/runtime/bootstrap.py`의 `create_dispatcher_context()`로 설정, ServiceFactory, Redis 클라이언트 주입.
- Redis: RQ 백엔드로 사용하며 `Queue("outbox")` 생성.
- Outbox 도메인: `svcs.outboxs.enqueue_outbox_pending(...)`가 DB의 pending 레코드를 큐로 밀어 넣음.
- Sentry/로깅: 서비스 레벨 로깅 및 오류 리포팅.

## Data Flow
1) Dispatcher 루프가 `svcs.outboxs.enqueue_outbox_pending(poll_limit, q_outbox)`를 호출해 pending Outbox를 가져옴.
2) 각 이벤트는 RQ Queue `outbox`에 태스크로 enqueue.
3) 워커 서비스가 같은 Redis를 백엔드로 RQ 워커를 실행해 태스크를 실제 처리.
4) 처리할 이벤트가 없으면 `idle_sleep` 동안 대기, 예외 발생 시 로그 후 재시도.

## Related Services
- **scheduler**: 주기적으로 Outbox 이벤트를 생성해 dispatcher가 폴링할 대상을 공급.
- **worker**: dispatcher가 큐잉한 `outbox` 작업을 실행(이메일 발송, 동기화, 스냅샷 등).
- **collector/api**: 간접적으로, worker가 처리한 결과(카탈로그/스냅샷/알림)가 이들 서비스에 반영됨.
