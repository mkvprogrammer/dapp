#!/usr/bin/env bash
# Production deploy on a Linux server (Docker Compose).
set -euo pipefail
cd "$(dirname "$0")/.."

ENV_FILE="infra/.env"
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file ${ENV_FILE}"

warn() { echo "WARNING: $*" >&2; }
die() { echo "ERROR: $*" >&2; exit 1; }

command -v docker >/dev/null || die "Docker is not installed"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is required"

# --- [1/6] Blockchain & infra bootstrap ---
if [ ! -f infra/genesis.json ]; then
  echo "==> [1/6] First-time setup (genesis, keys, infra/.env)..."
  docker compose build setup
  docker compose run --rm setup
else
  echo "==> [1/6] Genesis exists, skipping setup"
fi

[ -f "${ENV_FILE}" ] || die "${ENV_FILE} not found. Run setup first."

# --- [2/6] Merge optional production overrides ---
if [ -f .env.production ]; then
  echo "==> [2/6] Applying .env.production overrides..."
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line//$'\r'/}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    key="${line%%=*}"
    key="${key//[[:space:]]/}"
    [ -n "$key" ] || continue
    val="${line#*=}"
    if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
      sed -i "s|^${key}=.*|${key}=${val}|" "${ENV_FILE}"
    else
      echo "${key}=${val}" >> "${ENV_FILE}"
    fi
  done < .env.production
else
  echo "==> [2/6] No .env.production (optional). See .env.production.example"
fi

# --- [3/6] Secrets & production checks ---
echo "==> [3/6] Checking secrets..."
if ! grep -q '^JWT_SECRET_KEY=.\{16,\}' "${ENV_FILE}" 2>/dev/null; then
  if command -v openssl >/dev/null 2>&1; then
    secret="$(openssl rand -hex 32)"
    echo "JWT_SECRET_KEY=${secret}" >> "${ENV_FILE}"
    echo "    Generated JWT_SECRET_KEY"
  else
    die "Set JWT_SECRET_KEY in ${ENV_FILE} (openssl not found to auto-generate)"
  fi
fi

if grep -q '^DB_PASSWORD=devpass_secure_123' "${ENV_FILE}" 2>/dev/null; then
  warn "DB_PASSWORD is still the dev default — change it in ${ENV_FILE} before production use"
fi

if ! grep -q '^CORS_ORIGINS=' "${ENV_FILE}" 2>/dev/null; then
  warn "CORS_ORIGINS is not set — add your public URL to ${ENV_FILE}"
fi

# Ensure docker-internal hosts (setup may have written 127.0.0.1)
python3 docker/setup/patch_env.py "${ENV_FILE}" 2>/dev/null || true

# --- [4/6] Pull base images ---
if [ "${SKIP_IMAGE_PULL:-}" != "1" ]; then
  echo "==> [4/6] Pulling base images..."
  chmod +x scripts/pull-base-images.sh
  ./scripts/pull-base-images.sh
else
  echo "==> [4/6] Skipping image pull (SKIP_IMAGE_PULL=1)"
fi

# --- [5/6] Build & migrate ---
echo "==> [5/6] Building images..."
${COMPOSE} build

echo "==> [5/6] Database migrations..."
./scripts/migrate.sh

# --- [6/6] Start stack ---
echo "==> [6/6] Starting production stack..."
${COMPOSE} up -d --build

bind="$(grep -E '^FRONTEND_BIND=' "${ENV_FILE}" 2>/dev/null | cut -d= -f2- || echo 127.0.0.1)"
port="$(grep -E '^FRONTEND_PORT=' "${ENV_FILE}" 2>/dev/null | cut -d= -f2- || echo 80)"

echo ""
echo "Deploy finished."
echo "  UI:     http://${bind}:${port}/"
echo "  Health: http://${bind}:${port}/health"
echo "  Logs:   ${COMPOSE} logs -f"
echo ""
echo "Put TLS reverse proxy (nginx/Caddy) in front of ${bind}:${port} if exposed to the internet."
