#!/usr/bin/env bash
# Применяет Alembic-миграции к PostgreSQL (нужны infra/.env и образ backend).
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="infra/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Ошибка: нет $ENV_FILE. Сначала выполните setup (make up)." >&2
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE")

echo "==> Сборка образа backend (если нужно)..."
"${COMPOSE[@]}" build backend

echo "==> Запуск PostgreSQL для миграций..."
"${COMPOSE[@]}" up -d db

echo "==> Ожидание готовности PostgreSQL..."
for _ in $(seq 1 60); do
  if "${COMPOSE[@]}" exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "==> Alembic upgrade head ..."
"${COMPOSE[@]}" run --rm --no-deps backend alembic upgrade head

echo "==> Миграции применены."
