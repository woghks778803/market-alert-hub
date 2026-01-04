#!/usr/bin/env bash
set -euo pipefail

# RQ Worker 실행
# exec rq worker outbox
echo "[Worker] Starting Worker..."
exec python -m app.main
