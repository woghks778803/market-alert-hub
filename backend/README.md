# Backend

## Purpose
- 실시간 시세 수집부터 알림/배치 작업, API 노출까지를 담당하는 백엔드 서비스 모음. 각 서비스는 컨테이너로 분리되며 `common` 레이어를 공유해 일관된 도메인/인프라 로직을 사용한다.

## Service Overview
- `api`: FastAPI 기반 HTTP API 서비스. 인증/유저/알림 관련 엔드포인트를 제공하고 다른 서비스가 적재한 데이터(예: Redis, DB)를 노출한다.
- `collector`: 거래소 WS/REST에서 실시간 시세를 수집해 Redis 스냅샷/스트림으로 적재한다.
- `scheduler`: 주기 작업을 정의해 Outbox 이벤트를 생성(카탈로그 동기화, 스냅샷 적재 등)한다.
- `dispatcher`: Outbox의 pending 이벤트를 폴링해 RQ Queue로 전달, 워커가 소비할 수 있게 큐잉한다.
- `worker`: RQ 큐의 작업을 실행해 이메일/동기화/스냅샷 적재 등 백그라운드 잡을 수행한다.
- `common`: 모든 서비스가 사용하는 공유 애플리케이션 계층(도메인 규칙, 서비스/인프라 어댑터, 런타임 부트스트랩, 템플릿 등)을 제공한다.

## Processing Pipeline
1) **수집**: `collector`가 거래소 WS를 구독해 Redis에 시세 스냅샷/스트림을 기록.
2) **스케줄**: `scheduler`가 주기적으로 Outbox 이벤트(동기화·스냅샷 등)를 생성.
3) **디스패치**: `dispatcher`가 Outbox pending을 RQ Queue(`outbox`)로 큐잉.
4) **실행**: `worker`가 큐를 소비해 도메인 핸들러를 실행(이메일 발송, 동기화, 스냅샷 적재).
5) **노출**: `api`가 DB/Redis에 저장된 결과와 사용자 도메인 기능을 HTTP API로 제공.

## Directory Structure
- `backend/common/` : 공유 도메인·서비스·인프라·런타임 레이어
- `backend/api/` : API 서비스 소스
- `backend/collector/` : 시세 수집 서비스 소스
- `backend/scheduler/` : 주기 작업 스케줄러 소스
- `backend/dispatcher/` : Outbox → 큐 디스패처 소스
- `backend/worker/` : RQ 워커 실행기 소스
- `backend/db/` : MySQL 초기화/설정 파일
- `backend/redis/` : Redis 설정 파일
