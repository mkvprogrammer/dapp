#!/usr/bin/env bash
# Полный старт стека: генерация ключей → compose up (контракты, миграции, UI).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/5] Инициализация infra (genesis, ключи, .env)..."
docker compose build setup
docker compose run --rm setup

if [ ! -f infra/.env ]; then
  echo "Ошибка: infra/.env не создан. Проверьте логи setup." >&2
  exit 1
fi

if [ "${SKIP_IMAGE_PULL:-}" != "1" ]; then
  echo "==> [2/5] Загрузка базовых образов (Docker Hub)..."
  ./scripts/pull-base-images.sh
else
  echo "==> [2/5] Пропуск pull (SKIP_IMAGE_PULL=1)"
fi

echo "==> [3/5] Сборка образов..."
docker compose --env-file infra/.env build

echo "==> [4/5] Миграции БД (Alembic)..."
./scripts/migrate.sh

echo "==> [5/5] Запуск всех сервисов..."
exec docker compose --env-file infra/.env up --build "$@"
