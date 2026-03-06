# Market Alert Hub

실시간 크립토 시세를 수집·분석해 알림을 보내는 서비스입니다. 프런트는 Vue 3 SPA, 백엔드는 FastAPI 기반 마이크로서비스, 인프라는 Docker Compose(개발)와 Azure 컨테이너 기반 배포를 목표로 합니다.

## 아키텍처
- **클라이언트**: `frontend/` — Vue 3 + Vite + TypeScript, Pinia 상태관리, Vuetify UI. 빌드 산출물은 Nginx가 정적 서빙.
- **API 게이트웨이**: `gateway/nginx.conf` — `/api`·`/admin-api`를 API 서비스로 리버스 프록시, 나머지는 SPA 정적 파일을 반환.
- **백엔드 서비스** (`backend/`):
  - `api/`: FastAPI 메인 API. CORS, 요청 ID, Sentry, JWT 인증/권한, 퍼블릭·어드민 라우터 포함.
  - `collector/`: 거래소(Upbit) WS/REST로 시세 수집.
  - `dispatcher/`: 알림 발송 파이프라인 오케스트레이션.
  - `scheduler/`: 주기 작업 등록/실행.
  - `worker/`: 백그라운드 태스크 실행.
  - 공용 런타임(`backend/common/app/runtime`)이 DB/Redis 프로바이더, JWT 인증·토큰 서명, 데이터 암호화 유틸, 외부 연동(Kakao OAuth, AWS SES), 거래소 클라이언트(Upbit WS/REST) 같은 인프라 의존성을 묶어 서비스들에 주입.
- **데이터 스토어**: MySQL, Redis (개발 설정은 `backend/db/`, `backend/redis/`).
- **문서/의사결정**: `docs/` — SPA vs SSR, 알림 채널 우선순위 등 ADR; `infra/README.md`는 Azure 컨테이너 배포 절차 초안.

## System Architecture
Exchange → collector → Redis / Redis, Database → scheduler, API → dispatcher → worker → Database / Database → API → Frontend

## 로컬 개발 실행
```bash
# 1) 백엔드 인프라/서비스 (Docker Compose)
cd ops/dev
docker compose --env-file .env -f docker-compose.base.yml up -d

# 2) 프런트엔드 개발 서버
cd ../../frontend
npm install
npm run dev   # http://localhost:5173
```

## 코드 베이스 가이드
- 프런트 엔트리: `frontend/src/main.ts`; 라우트 `frontend/src/routes/`; 주요 화면 `frontend/src/views/app/…`; 인증 스토어 `frontend/src/stores/auth.store.ts`.
- API 엔트리: `backend/api/app/main.py`; 인증·DI: `backend/api/app/api/deps.py`; 라우터: `backend/api/app/api/router/`.
- 서비스 공통 설정·프로바이더: `backend/common/app/runtime/`.
- Nginx 설정: `gateway/nginx.conf`.
- 배포/운영 문서: `docs/`, `infra/`.

## 향후 보완
- API 명세(`docs/API-Contracts.md`)와 서비스별 README 확충
- 테스트/린트 파이프라인 추가
- 배포용 CI/CD 및 관찰성 대시보드 정리
