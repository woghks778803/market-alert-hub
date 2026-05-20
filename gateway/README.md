# Gateway (Nginx)

## Purpose
- 단일 진입점으로서 프런트엔드 SPA를 정적 서빙하고, 백엔드 API 요청을 내부 서비스로 프록시한다.

## Responsibilities
- `frontend/dist` 빌드 산출물을 정적 파일로 제공.
- `/api/`, `/admin-api/` 트래픽을 FastAPI `api` 서비스로 라우팅.
- 기본 헬스 체크 엔드포인트(`/healthz`) 제공.

## Configuration
- 설정 파일: `gateway/nginx.conf`.
- 정적 루트: `/usr/share/nginx/html`에 배포된 SPA 파일을 `index.html` 기본 문서로 서빙.
- 워커/커넥션 등 일반 Nginx 기본 설정 포함.

## Routing
- `/api/` → `http://api:8000` (Docker Compose 네트워크의 `api` 컨테이너)
- `/admin-api/` → `http://api:8000`
- `/healthz` → 200 OK 텍스트 응답
- 나머지 경로는 SPA 정적 파일로 처리(미스 시 404).

## Related Services
- **frontend**: 빌드 결과물을 Nginx 루트에 배포해 사용자에게 전달.
- **backend/api**: `/api`와 `/admin-api` 프록시 타겟으로 동작.
