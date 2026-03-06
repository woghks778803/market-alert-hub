# Worker Service

## Purpose
- Redis RQ 큐에서 작업을 소비하여 도메인 백그라운드 작업(동기화, 스냅샷 적재, 인증 메일/비밀번호 재설정 등)을 실행하는 워커 서비스

## Responsibilities
- RQ 워커 프로세스를 기동하여 `outbox` 큐의 잡을 처리.
- Outbox 이벤트를 도메인 핸들러에 매핑하고, 성공/재시도/스킵/치명 오류 정책을 적용.
- 이메일·알림 발송, 거래소/심볼 동기화, 스냅샷 적재 등 다양한 작업을 공용 도메인 서비스로 위임.
- Sentry/로깅과 락/리트라이를 활용해 안정적으로 실행.

## Entrypoint
- `app/main.py` → `app/run.py`.
- `app/wiring.py`가 `create_worker_context()`로 공용 컨텍스트(ServiceFactory, WorkerConfigBag, Redis 연결)를 불러와 RQ Queue(`outbox`)와 함께 `WorkerRuntime`을 구성.
- `app/run.py`에서 RQ `Worker([q_outbox])`를 생성, 신호(SIGTERM/SIGINT) 처리 후 `worker.work(with_scheduler=True)`로 실행.

## Dependencies
- 공용 런타임: `backend/common/app/runtime/bootstrap.create_worker_context()`로 ServiceFactory, Redis 클라이언트, 설정(ConfigBag) 주입.
- Redis: RQ 백엔드와 락(중복 발송 방지) 등에 사용.
- Outbox 도메인: `ctx.svcs.outboxs.deliver_outbox`가 상태 전이와 재시도 정책을 관리.
- Sentry/로깅: 서비스 레벨 로깅 및 오류 리포팅.

## Data Flow
1) Dispatcher가 Outbox pending을 RQ Queue `outbox`로 enqueue.
2) Worker 프로세스가 큐에서 `deliver_outbox_event(outbox_id)` 잡을 가져와 실행.
3) `deliver_outbox_event`가 OutboxService에 전달하고, OutboxService가 이벤트 유형에 따라 핸들러를 호출.
4) `tasks.py`의 매핑이 이벤트 유형 → 핸들러(`handler/*`)로 연결:  
   - AUTH_EMAIL_VERIFY / AUTH_PASSWORD_RESET → 이메일 발송  
   - SYNC_EXCHANGES / SYNC_SYMBOLS → 카탈로그 동기화  
   - PERSIST_SNAPSHOTS → 시세 스냅샷 적재  
5) 핸들러는 공용 서비스/인프라(SES, Redis, DB 등)를 사용하고, 필요 시 락과 재시도 예외로 흐름을 제어.

## Related Services
- **dispatcher**: Outbox를 큐에 넣어 worker가 소비하도록 전달.
- **scheduler**: 주기적 이벤트를 Outbox에 쌓아 worker 작업을 발생시킴.
- **collector**: 동기화/스냅샷 결과를 활용해 WS 구독 및 데이터 제공.
- **api**: 이메일 인증/비번 재설정 등 사용자 작업 완료 상태를 조회하거나 트리거할 수 있음.
