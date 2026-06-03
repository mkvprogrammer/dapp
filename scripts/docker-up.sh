#!/usr/bin/env bash
# Полный старт стека: генерация ключей → compose up (контракты, миграции, UI).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "==> [1/2] Инициализация infra (genesis, ключи, .env)..."
docker compose build setup
docker compose run --rm setup

if [ ! -f infra/.env ]; then
  echo "Ошибка: infra/.env не создан. Проверьте логи setup." >&2
  exit 1
fi

echo "==> [2/2] Запуск всех сервисов..."
exec docker compose --env-file infra/.env up --build "$@"
