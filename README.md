# UniDApp (AuctionChain)

Университетская платформа аукционов на приватной PoA-сети: распределение ограниченных ресурсов (консультации, аудитории, оборудование) через ставки во внутренних токенах проекта.

| Компонент | Технологии |
|-----------|------------|
| API | FastAPI, SQLAlchemy 2, Alembic, PyJWT |
| БД | PostgreSQL, Redis (Celery) |
| Блокчейн | Geth Clique PoA, Web3.py, Hardhat, Solidity (ERC-1155) |
| UI | React (Vite), nginx |
| Запуск | Docker Compose |

---

## Архитектура

```
[ Browser ] → nginx (frontend) → FastAPI (backend)
                                    ↓
              PostgreSQL · Redis · Geth RPC · смарт-контракты
```

| Слой | Каталог | Назначение |
|------|---------|------------|
| API | `backend/app/api/` | HTTP, JWT, делегирование в сервисы |
| Сервисы | `backend/app/services/` | Бизнес-логика, relayer, аукционы |
| ORM | `backend/app/models/` | Пользователи, проекты, аукционы |
| Контракты | `smartcontracts/contracts/` | `UniversityToken`, `ProjectRegistry`, `AuctionManager` |

Роли API: `admin`, `organizer`, `student`. Токены разных проектов изолированы (ERC-1155, `projectId` как token id).

---

## Локальный запуск (разработка)

### Требования

- Docker и Docker Compose v2.24+ (для production overlay с `ports: !reset`)
- 4+ ГБ RAM, 10+ ГБ диск

### Команды

```bash
git clone <repository-url>
cd dapp
make up
```

Первый запуск: генерация genesis и ключей, сборка образов, деплой контрактов, миграции Alembic.

| Сервис | URL (по умолчанию) |
|--------|-------------------|
| UI | http://localhost:3001 |
| API / Swagger | http://localhost:8001/docs |
| Health | http://localhost:8001/health |
| PostgreSQL | localhost:5433 |
| PgAdmin | http://localhost:8081 (`admin@admin.com` / `adminpassword`) |

```bash
make down          # остановка
make logs          # логи
make pull-images   # повторная загрузка образов с Hub
make migrate       # только Alembic
make reset         # полный сброс данных (БД, ноды, ключи)
```

При `TLS handshake timeout` при pull: `make pull-images`, зеркало `DOCKER_MIRROR=docker.m.daocloud.io/library make pull-images`, затем `make up`. Обход pull: `SKIP_IMAGE_PULL=1 make up`.

Порядок старта: `setup` → Geth → `contracts` → `backend` (миграции + API) → `frontend` (прокси `/api` на backend).

---

## Развёртывание на сервере

Подготовлено для типичного сценария: Linux-сервер, Docker, TLS через внешний nginx/Caddy. Наружу публикуется только фронтенд (порт задаётся в `infra/.env`); PostgreSQL, Redis, Geth и прямой порт API не пробрасываются.

### 1. Подготовка сервера

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# перелогиньтесь
```

Откройте в firewall только 80/443 (reverse proxy). Порт приложения (`FRONTEND_PORT`, по умолчанию 80 на `127.0.0.1`) не обязан быть доступен из интернета.

### 2. Клонирование и конфигурация

```bash
git clone <repository-url>
cd dapp

# Опционально: переопределения для продакшена (пароли, домен, JWT)
cp .env.production.example .env.production
# Отредактируйте .env.production: CORS_ORIGINS, DB_PASSWORD, домен
```

Файл `infra/.env` создаётся автоматически при первом деплое (`setup`). Скрипт `deploy-server.sh` подмешивает `.env.production`, если он есть, и генерирует `JWT_SECRET_KEY`, если не задан.

Обязательно перед боевым запуском:

| Переменная | Действие |
|------------|----------|
| `JWT_SECRET_KEY` | Случайная строка (`openssl rand -hex 32`) |
| `DB_PASSWORD` | Не оставлять `devpass_secure_123` |
| `CORS_ORIGINS` | Публичный URL, например `https://auction.example.edu` |
| `DEBUG` | `false` |
| `ALLOW_DEMO_TOPUP` | `false` |
| `FRONTEND_BIND` | `127.0.0.1` при reverse proxy на том же хосте |

### 3. Запуск

```bash
make prod-up
# или: ./scripts/deploy-server.sh
```

Проверка:

```bash
curl -sS http://127.0.0.1/health
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file infra/.env ps
make prod-logs
```

Остановка: `make prod-down`.

### 4. TLS и reverse proxy

Пример конфигурации nginx на хосте: [`deploy/nginx-reverse-proxy.example.conf`](deploy/nginx-reverse-proxy.example.conf).

Схема:

```
Internet → nginx (443) → 127.0.0.1:80 (контейнер frontend)
                              ↳ /api → backend:8000
```

UI ходит в API по тому же origin (`/api/...`), отдельный `VITE_API_URL` на сервере не нужен.

### 5. Обновление версии

```bash
git pull
make prod-up
```

Миграции выполняются в `deploy-server.sh` и при старте контейнера `backend`.

### 6. Резервное копирование

- Том Docker `pgdata` — PostgreSQL
- Том `uploads_data` — загруженные изображения (`docker-compose.prod.yml`)
- `infra/node1_data`, `infra/node2_data` — блокчейн (при сбросе потребуется повторный деплой контрактов)
- `smartcontracts/deployed.json` — адреса контрактов (генерируется сервисом `contracts`)

Не коммитьте в git: `infra/.env`, `infra/scripts/generated_keys.json`, `infra/genesis.json`, `smartcontracts/deployed.json`.

### 7. PgAdmin (только отладка)

В production PgAdmin отключён (profile `dev-tools`). Для доступа к БД используйте `docker compose exec db psql` или временно:

```bash
docker compose --profile dev-tools -f docker-compose.yml -f docker-compose.prod.yml --env-file infra/.env up -d pgadmin
```

---

## Ручная установка (без полного Compose)

Используйте, если API и UI запускаются локально, а инфраструктура — в Docker.

1. `cd infra && python -m venv venv && pip install -r requirements.txt && python scripts/setup.py`
2. `docker compose up -d` в `infra/` — Geth и PostgreSQL
3. `cd smartcontracts && npm ci && npx hardhat compile && npx hardhat run scripts/deploy.js --network localPoA`
4. Скопируйте ключи из `infra/scripts/generated_keys.json` в `smartcontracts/.env` и `BLOCKCHAIN_ADMIN_PRIVATE_KEY` в `infra/.env`
5. `cd backend && pip install -r requirements.txt && alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000`
6. `cd frontend && npm ci && npm run dev` (прокси API — см. `vite.config.js`)

---

## Безопасность

- JWT: access (короткий TTL) + refresh с ротацией; в БД хранится только SHA-256 refresh.
- Кошельки: приватный ключ шифруется паролем пользователя (Fernet); на регистрации ключ показывается один раз.
- Web3: для Clique PoA обязателен `geth_poa_middleware` (`backend/app/core/blockchain.py`).
- Проценты: в PostgreSQL — `Numeric`; в Solidity — basis points (10 000 = 100%).

---

## CLI (backend/scripts)

```bash
cd backend && source venv/bin/activate
python scripts/check_roles.py [0xAddress]
python scripts/get_token_balance.py [0xAddress] [project_token_id]
```

Требуются запущенная нода и `infra/.env`.

---

## API

После запуска backend: Swagger на `/docs`. Авторизация: `POST /api/v1/auth/login` → `Authorize` → `Bearer <access_token>`.

Основные группы: `auth`, `dashboard`, `users`, `projects`, `auctions`, `attendance`, `transfers`, `notifications`, `wallet`, `admin`, `uploads`.

---

## Структура репозитория

```
dapp/
├── docker-compose.yml          # полный стек (разработка)
├── docker-compose.prod.yml     # overlay для сервера
├── .env.production.example     # шаблон продакшен-переменных
├── deploy/                     # пример nginx
├── scripts/                    # docker-up.sh, deploy-server.sh, migrate.sh
├── infra/                      # genesis, setup.py, локальный compose
├── smartcontracts/             # Hardhat, контракты
├── backend/                    # FastAPI, Alembic
└── frontend/                   # React UI
```

---

## Лицензия

См. файл `LICENSE` в корне репозитория.
