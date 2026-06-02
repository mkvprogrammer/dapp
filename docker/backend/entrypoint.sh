#!/bin/sh
set -eu

echo "==> Waiting for PostgreSQL at ${DB_HOST:-db}:${DB_PORT:-5432} ..."
python - <<'PY'
import os, socket, time
host = os.environ.get("DB_HOST", "db")
port = int(os.environ.get("DB_PORT", "5432"))
for _ in range(60):
    try:
        s = socket.create_connection((host, port), 2)
        s.close()
        break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL not reachable")
PY

echo "==> Alembic upgrade head ..."
alembic upgrade head

echo "==> Starting FastAPI ..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
