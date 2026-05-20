#!/usr/bin/env bash
set -euo pipefail

# Scheduler 실행
echo "[Scheduler] Starting Scheduler..."
exec python -m app.main
