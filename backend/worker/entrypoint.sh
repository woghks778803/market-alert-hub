#!/usr/bin/env bash
set -euo pipefail

# RQ Worker 실행
# exec rq worker outbox
exec python -m app.main
