#!/usr/bin/env bash
set -euo pipefail

# Outbox Dispatcher 실행
echo "[Dispatcher] Starting Outbox Dispatcher..."
exec python -m app.main
