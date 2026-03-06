# Ops

## Purpose
- 로컬 개발 및 배포 환경을 위한 Docker Compose 구성과 환경변수 관리 파일을 포함하는 디렉터리.

## Directory Structure
- `ops/dev/`
  - `docker-compose.base.yml`: 로컬 개발 기본 스택(gateway, api, worker, dispatcher, scheduler, collector, db, redis).
  - `docker-compose.local.yml`: 필요 시 추가 오버레이/로컬 커스터마이즈.
  - `env/`: 서비스별 환경 변수 파일(common, api, worker, dispatcher, scheduler, collector, gateway).
  - `.env.example`: 공통 환경 변수 템플릿(루트에 위치).
- `ops/prod/`
  - 현재 비어 있음. 향후 운영 배포용 Compose 또는 IaC 템플릿을 배치할 예정인 디렉터리.

## Development Environment
- `ops/dev/docker-compose.base.yml`를 기준으로 `docker compose --env-file .env -f docker-compose.base.yml up` 형태로 구동.
- 각 서비스는 `env/common.env`와 서비스 전용 env 파일을 로드해 DB/Redis/AWS/JWT 등 설정을 주입.
- `docker-compose.local.yml`로 포트·볼륨·디버깅 설정을 추가 오버라이드 가능.

## Production Environment
- `ops/prod/`는 아직 템플릿만 존재(빈 상태). 동일한 구조로 compose/IaC를 배치해 사용할 수 있도록 예약된 디렉터리.

## Environment Variables
- 루트 `.env` / `.env.example`에서 공통 변수(DB, Redis, AWS, JWT, Crypto 등) 기본값을 정의.
- 서비스별 세부 설정은 `ops/dev/env/*.env`로 분리해 주입하며, compose의 `env_file`로 불러온다.
