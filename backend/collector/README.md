# Collector Service

## Purpose
- 거래소 WebSocket 스트림에서 실시간 시세를 수집하여 Redis에 스냅샷·스트림 형태로 적재하는 수집 전용 서비스.
- 공통 도메인/인프라 계층(`backend/common`)을 활용해 다른 서비스와 동일한 설정·클라이언트·도메인 규칙을 공유.

## Responsibilities
- 활성 종목 목록을 주기적으로 조회해 거래소 WS 구독을 유지·갱신.
- 수신한 틱 데이터를 Redis 해시(SNAP)와 스트림(STREAM)으로 저장해 최신 값과 최근 히스토리를 제공.
- 체크포인트를 저장해 재시작 시 커서 기반 재구독을 지원.
- 장애 시 백오프 정책으로 자동 재연결 및 태스크 수준 감시.

## Entrypoint
- `app/main.py`: 로깅·Sentry 초기화 후 `build_runtime()`으로 런타임 구성, `asyncio.run(run(runtime))` 실행.
- `app/wiring.py`: 설정을 읽어 CollectorRuntime을 조립(컨텍스트, 체크포인트 스토어, 재시작 정책, 작업 스펙).
- `app/run.py`: OS 신호를 받아 stop_event를 관리하고, supervised 태스크들을 실행/정리.

## Dependencies
- 공용 런타임: `backend/common/app/runtime/bootstrap.py`의 `create_collector_context()`로 Redis async 클라이언트, Upbit WS/REST, ActiveMarketCatalog, 설정(ConfigBag) 등을 주입.
- Redis: async 클라이언트로 스냅샷/스트림 저장, 키 TTL/trim 관리.
- 외부 거래소: WS 팩토리/구독 팩토리(`ctx.ws_facs_register`, `ctx.subscribe_facs_register`)를 통해 Upbit 등으로 연결.
- 체크포인트 스토어: 기본 메모리, 설정에 따라 파일(`FileCheckpointStore`).
- Sentry/로깅: 서비스 레벨 로깅 및 오류 리포팅.

## Data Flow
1) 런타임이 `ws_facs_register`와 `subscribe_facs_register`에 등록된 거래소별로 시장 스트림 태스크를 생성.
2) 각 태스크(`run_stream_marketdata_loop`)는 ActiveMarketCatalog에서 심볼 스냅샷을 주기적으로 읽어 현재 구독 목록을 유지.
3) 거래소 WS로부터 받은 메시지를 `upsert_marketdata_and_buffer_5m`에서 처리:
   - 해시 스냅샷 키: `{app}:{env}:snap:ticker:{exchange}`에 심볼별 최신 payload 저장.
   - 스트림 키: `{app}:{env}:stream:ticker:{exchange}:{symbol}`에 ts/payload를 추가, 최대 길이/TTL 관리.
4) 커서(체크포인트)를 저장해 재구독 시 이어서 처리.
5) 에러 발생 시 지정된 백오프 정책으로 재연결하며, stop_event 설정 시 태스크를 정리.

## Related Services
- **dispatcher / worker**: Redis에 적재된 ticker 스냅샷·스트림을 읽어 알림 트리거/전송 등에 활용.
- **api**: 필요 시 Redis 스냅샷을 조회하거나, ActiveMarketCatalog를 통해 심볼 정보를 제공.
- **scheduler**: 심볼/거래소 카탈로그 동기화 작업으로 collector가 구독할 대상 목록을 최신으로 유지.
