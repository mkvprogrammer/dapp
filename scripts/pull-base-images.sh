#!/usr/bin/env bash
# Предзагрузка базовых образов с повторами (обход TLS timeout к registry-1.docker.io).
set -euo pipefail

RETRIES="${PULL_RETRIES:-5}"
SLEEP="${PULL_SLEEP_SEC:-8}"

IMAGES=(
  node:20-bookworm-slim
  nginx:1.27-alpine
  python:3.12-slim
  postgres:15-alpine
  redis:7-alpine
  ethereum/client-go:v1.13.15
  dpage/pgadmin4:latest
)

pull_image() {
  local img="$1"
  local ref="$img"

  # Пример: DOCKER_MIRROR=docker.m.daocloud.io/library → docker.m.daocloud.io/library/node:20-bookworm-slim
  if [ -n "${DOCKER_MIRROR:-}" ]; then
    ref="${DOCKER_MIRROR%/}/${img}"
  fi

  local attempt=1
  while [ "$attempt" -le "$RETRIES" ]; do
    echo "==> pull $ref (попытка $attempt/$RETRIES)"
    if docker pull "$ref"; then
      if [ "$ref" != "$img" ]; then
        docker tag "$ref" "$img"
        echo "    tagged as $img"
      fi
      return 0
    fi
    attempt=$((attempt + 1))
    if [ "$attempt" -le "$RETRIES" ]; then
      echo "    повтор через ${SLEEP}s…"
      sleep "$SLEEP"
    fi
  done
  return 1
}

failed=0
for img in "${IMAGES[@]}"; do
  if ! pull_image "$img"; then
    echo "Ошибка: не удалось скачать $img" >&2
    failed=1
  fi
done

if [ "$failed" -ne 0 ]; then
  echo "" >&2
  echo "Docker Hub недоступен или очень медленный. Варианты:" >&2
  echo "  1) Повторите: ./scripts/pull-base-images.sh" >&2
  echo "  2) Зеркало: DOCKER_MIRROR=docker.m.daocloud.io/library ./scripts/pull-base-images.sh" >&2
  echo "  3) В /etc/docker/daemon.json добавьте registry-mirrors и перезапустите docker" >&2
  echo "  4) VPN / другая сеть, затем make up" >&2
  exit 1
fi

echo "==> Все базовые образы загружены."
