#!/bin/bash
set -e

if [ "${RUN_ALEMBIC:-0}" = "1" ]; then
  echo "[api] running alembic migrations..."
  alembic -c /app/alembic.ini upgrade head || echo "[api] alembic failed"
else
  echo "[api] skip alembic"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/app
