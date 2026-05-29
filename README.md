# 🚀 UniDApp API

**Университетская экосистема аукционов на приватной блокчейн-сети PoA.**

UniDApp — децентрализованная платформа для честного распределения ограниченных ресурсов в университете: записи на защиту работ, бронирования коворкингов, слотов на лабораторные и другие дефицитные активности. Участники делают ставки внутренними токенами проекта; победители получают доступ к ресурсу, а система штрафов и возвратов мотивирует ответственное поведение.

**Стек технологий:**

- **FastAPI** — асинхронный REST API и Swagger-документация
- **SQLAlchemy 2.0** — ORM и миграции через Alembic
- **PostgreSQL** — реляционное хранилище метаданных и сессий
- **Web3.py** — интеграция с Geth и смарт-контрактами
- **Hardhat** — компиляция, тестирование и деплой Solidity-контрактов
- **Docker Compose** — PoA-ноды, PostgreSQL, Redis, PgAdmin
- **PyJWT** — access/refresh JWT с ротацией
- **Passlib** — bcrypt-хэширование паролей

---

## 🏛️ Архитектура системы

UniDApp построен по классической многослойной схеме. Каждый слой решает одну задачу и не смешивает ответственность.

```
[ Frontend ]  →  HTTP/WS
[ FastAPI API ]  →  PostgreSQL · Redis · Geth RPC
[ Smart Contracts ]  →  Clique PoA Blockchain
```

### Слои приложения

| Слой | Расположение | Назначение |
|------|--------------|------------|
| **API (веб-ручки)** | `backend/app/api/` | Маршрутизация HTTP, OAuth2 Bearer, делегирование в сервисы |
| **Сервисы (бизнес-логика)** | `backend/app/services/` | Регистрация, аукционы, проекты, on-chain relayer |
| **Валидация Pydantic** | `backend/app/schemas/` | Входные/выходные DTO, отсечение секретных полей |
| **ORM SQLAlchemy** | `backend/app/models/` | Пользователи, проекты, аукционы, refresh-токены |
| **Web3-клиент** | `backend/app/core/blockchain.py` | Singleton Web3, ABI из Hardhat-артефактов, подпись транзакций |

**Конвейер запроса:** JSON → Pydantic-схема → Сервис → SQLAlchemy ORM / Web3 → Pydantic `response_model` → JSON.

### Смарт-контракты

| Контракт | Стандарт | Роль |
|----------|----------|------|
| `UniversityToken.sol` | ERC-1155 | Мультитокены: каждый `projectId` — отдельный баланс |
| `ProjectRegistry.sol` | AccessControl | Реестр курсов, штрафы, лимиты, права организаторов |
| `AuctionManager.sol` | AccessControl | Аукционы: блокировка токенов, ставки, штрафы, возвраты |

### Ролевая модель (RBAC)

Права распределены на двух уровнях: **PostgreSQL (роль пользователя API)** и **OpenZeppelin AccessControl (on-chain роли)**.

| Роль API | On-chain роль | Права |
|----------|---------------|-------|
| **Admin** | `DEFAULT_ADMIN_ROLE` | Назначение организаторов, emergency-операции, mint от имени платформы |
| **Organizer / Teacher** | `ORGANIZER_ROLE` | Создание проектов, настройка правил, генерация кодов, аукционы |
| **Student** | `USER_ROLE` (AuctionManager) | Участие в аукционах, ставки, P2P-переводы внутри проекта |

> **Важно:** токены разных проектов **изолированы**. ERC-1155 хранит балансы в двумерной таблице `projectId → address → amount`.

---

## 🛠️ Предварительные требования

Перед развёртыванием убедитесь, что установлено:

| Инструмент | Минимальная версия | Назначение |
|------------|-------------------|------------|
| **Python** | 3.11+ | Backend, скрипты infra |
| **Node.js** | 18+ | Hardhat, деплой контрактов |
| **Docker Desktop** | актуальная | Geth-ноды, PostgreSQL, Redis, PgAdmin |
| **Git** | любая актуальная | Клонирование репозитория |

**Опционально:** `curl` — для проверки RPC-нод без браузера.

---

## ⚙️ Быстрое развертывание

### Шаг 1. Клонирование и настройка окружения

```bash
git clone https://github.com/mkvprogrammer/dapp.git
cd dapp
```

#### `infra/.env` — инфраструктура и БД

Файл **генерируется автоматически** скриптом `setup.py`. Ниже — структура переменных (см. также `infra/.env.example`):

```env
# --- PoA Blockchain ---
VALIDATOR_1_ADDRESS=0x...
VALIDATOR_2_ADDRESS=0x...
BLOCKCHAIN_URL="http://127.0.0.1:8541"
BLOCKCHAIN_ADMIN_PRIVATE_KEY="..."   # validator1.private_key из generated_keys.json

# --- P2P / Bootnodes ---
BOOTNODES=enode://...@172.30.0.10:30303,enode://...@172.30.0.20:30304

# --- PostgreSQL ---
DB_USER=dev
DB_PASSWORD=devpass_secure_123
DB_NAME=unidapp
DB_HOST=127.0.0.1
DB_PORT=5433
```

#### `smartcontracts/.env` — ключи для деплоя

Создайте файл по образцу `smartcontracts/.env.example`. Три приватных ключа берутся из `infra/scripts/generated_keys.json`:

```env
LOCAL_POA_DEPLOYER_KEY=0x...
LOCAL_POA_ORGANIZER_KEY=0x...
LOCAL_POA_RELAYER_KEY=0x...
```

> **Совет:** после `setup.py` скопируйте ключи deployer / organizer / relayer в `smartcontracts/.env`, а `validator1.private_key` — в `BLOCKCHAIN_ADMIN_PRIVATE_KEY` в `infra/.env`.

---

### Шаг 2. Инициализация и запуск блокчейн-сети

```bash
cd infra

# Виртуальное окружение для Python-скриптов
python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
# source venv/bin/activate

pip install -r requirements.txt

# Генерация genesis.json, keystore валидаторов, .env и generated_keys.json
python scripts/setup.py

# Запуск PoA-сети + PostgreSQL + Redis + PgAdmin
docker compose up -d
```

**RPC-эндпоинты:**

| Нода | HTTP RPC |
|------|----------|
| Node 1 (Validator 1) | `http://localhost:8541` |
| Node 2 (Validator 2) | `http://localhost:8542` |

**Проверка работоспособности сети:**

```bash
# Номер блока (result — hex-номер блока)
curl -X POST http://localhost:8541 \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}"

# Список аккаунтов (не пустой массив)
curl -X POST http://localhost:8541 \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_accounts\",\"params\":[],\"id\":1}"

# Gas price = 0 (бесплатная сеть)
curl -X POST http://localhost:8541 \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_gasPrice\",\"params\":[],\"id\":1}"

# Пиринг: node1 видит node2 (172.30.0.20)
curl -X POST http://localhost:8541 \
  -H "Content-Type: application/json" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"admin_peers\",\"params\":[],\"id\":1}"
```

> В логах Docker допустимы сообщения `WARN` и `Block failed` — это нормально для Clique PoA: ноды генерируют блоки поочерёдно, и каждая вторая попытка «лишней» ноды будет отклонена.

**Остановка сети:**

```bash
docker compose down
```

---

### Шаг 3. Деплой смарт-контрактов

```bash
cd ../smartcontracts

npm install
npm install dotenv --save-dev
npm install @openzeppelin/contracts

# Компиляция Solidity → ABI + bytecode в artifacts/
npx hardhat compile

# Деплой в localPoA (Docker-ноды должны быть запущены!)
npx hardhat run scripts/deploy.js --network localPoA
```

**Результат деплоя:**

- `smartcontracts/artifacts/contracts/` — ABI и bytecode (используются backend и CLI-скриптами)
- `smartcontracts/deployed.json` — адреса `ProjectRegistry`, `UniversityToken`, `AuctionManager` и назначенные роли

**Опционально — smoke-тест после деплоя:**

```bash
npx hardhat run scripts/TestAfterDeployContractsToPoA.js --network localPoA
```

**Полезные команды Hardhat:**

```bash
npx hardhat test      # прогон всех тестов
npx hardhat clean     # очистка кэша компиляции
```

---

### Шаг 4. Настройка и миграции базы данных

```bash
cd ../backend

# Новое venv для backend (отдельно от infra)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
```

Убедитесь, что контейнер PostgreSQL запущен:

```bash
cd ../infra
docker compose up -d db
```

Примените миграции Alembic из каталога `backend/`:

```bash
cd ../backend

# Создание новой миграции (при изменении моделей в app/models/)
alembic revision --autogenerate -m "описание изменений"

# Применение всех миграций
alembic upgrade head

# Проверка текущей ревизии
alembic current
```

> Новые модели добавляйте в `app/models/` и **импортируйте** в `app/models/__init__.py`, иначе autogenerate их не увидит.

**PgAdmin** (визуальный доступ к БД):

1. Откройте [http://localhost:8080](http://localhost:8080)
2. Логин: `admin@admin.com` / `adminpassword`
3. **Register Server** → Host: `db`, Port: `5432`, Database: `unidapp`, User: `dev`, Password: `devpass_secure_123`

---

### Шаг 5. Запуск бэкенда FastAPI

```bash
cd backend
venv\Scripts\activate

# Вариант 1 — через uvicorn с hot-reload
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Вариант 2 — через точку входа
python main.py
```

**Проверка:**

| URL | Описание |
|-----|----------|
| [http://localhost:8000](http://localhost:8000) | Корневой эндпоинт |
| [http://localhost:8000/health](http://localhost:8000/health) | Health-check (PostgreSQL) |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI |

---

### 🔄 Полный сброс блокчейн-сети

Если нужно пересоздать сеть с нуля:

```bash
cd infra
docker compose down
# Удалите папки node1_data и node2_data
venv\Scripts\activate
python scripts/setup.py
docker compose up -d

cd ../smartcontracts
# Обновите .env ключами из infra/scripts/generated_keys.json
npx hardhat run scripts/deploy.js --network localPoA

# Обновите BLOCKCHAIN_ADMIN_PRIVATE_KEY в infra/.env
cd ../backend
alembic upgrade head
python main.py
```

---

## 🔒 Особенности безопасности и Web3-логики

### Refresh Token Rotation

UniDApp использует **парную схему JWT**:

- **Access Token** — короткоживущий (по умолчанию 30 мин), передаётся в заголовке `Authorization: Bearer <token>`
- **Refresh Token** — долгоживущий (7 дней), используется только для получения новой пары

**Ротация при обновлении:**

1. Клиент отправляет refresh-токен на `/api/v1/auth/refresh`
2. Backend ищет **SHA-256 хэш** токена в таблице `refresh_tokens`
3. Если токен валиден и не отозван — он **немедленно помечается `is_revoked = True`**
4. Выпускается **новая пара** access + refresh; новый refresh сохраняется в БД

Это защищает от **replay-атак**: украденный refresh-токен можно использовать только один раз. Повторное использование отозванного токена отклоняется.

> Сырой refresh-токен **никогда не хранится** в PostgreSQL — только его хэш.

---

### Полукастодиальные кошельки (Semi-Custodial Wallets)

При регистрации backend:

1. Генерирует EOA-кошелёк через `eth_account.Account.create()`
2. Шифрует приватный ключ **паролем пользователя** (не хэшем!) алгоритмом **Fernet (AES-128-CBC + HMAC-SHA256)**
3. Сохраняет в БД только `wallet_address` и `encrypted_private_key`
4. Возвращает расшифрованный ключ **один раз** на фронтенд (для экспорта / резервной копии)

**KDF:** PBKDF2-HMAC-SHA256, 100 000 итераций → ключ Fernet.

При on-chain операциях (ставка, создание проекта) пользователь передаёт пароль; backend расшифровывает ключ **в памяти сессии**, подписывает транзакцию и не сохраняет ключ в открытом виде.

> **Компромисс UX / безопасность:** пользователю не нужен MetaMask и газ на балансе (relayer + gasPrice=0), но доверие к backend обязательно для хранения зашифрованного ключа.

---

### `geth_poa_middleware` — обязателен для Clique PoA

Стандартный алгоритм расчёта `blockHash` в Ethereum (PoW/PoS) **не совместим** с PoA-сетями (Clique, Aura). Geth в PoA записывает в поле `extraData` подпись валидатора, из-за чего Web3.py без middleware:

- возвращает **неверный block hash**
- некорректно обрабатывает **nonce** и **receipt**
- может «терять» транзакции после `send_raw_transaction`

**Решение** — инъекция middleware при инициализации Web3:

```python
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8541"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
```

Используется во всех точках: `blockchain.py`, `check_roles.py`, `get_token_balance.py`.

---

### Проценты в БД vs Basis Points в Solidity

| Контекст | Формат | Пример «80% возврата» |
|----------|--------|----------------------|
| **PostgreSQL** | `Numeric(5, 2)` — человекочитаемые проценты | `80.00` |
| **Solidity** | Basis Points (BPS), `100% = 10 000` | `8000` |

**Конвертация на backend** (`project_service.py`):

```python
def _decimal_to_basis_points(rate: Decimal) -> int:
    return int(rate * 100)   # 80.00 → 8000 bps
```

**В контракте** штрафы и возвраты считаются так:

```solidity
uint256 penaltyAmount = (bidAmount * penaltyPercent) / BASIS_POINTS;  // BASIS_POINTS = 10_000
```

> **Почему BPS on-chain?** Целочисленная арифметика без ошибок округления `float`; стандарт DeFi для процентных ставок, комиссий и штрафов.

---

## 📡 Проверка и администрирование (CLI)

Утилиты в `backend/scripts/` работают автономно: читают `infra/.env`, подключаются к RPC и загружают ABI из Hardhat-артефактов.

### `check_roles.py` — проверка on-chain ролей

Проверяет `DEFAULT_ADMIN_ROLE`, `ORGANIZER_ROLE` и `USER_ROLE` для указанного адреса.

```bash
cd backend
venv\Scripts\activate

# Интерактивный режим (выбор контракта 1–3)
python scripts/check_roles.py

# С адресом аргументом
python scripts/check_roles.py 0xCf3EE4870EC092cD1F28291AB6cd8fDbD0EBBB25
```

**Доступные контракты:**

| № | Контракт | Роли |
|---|----------|------|
| 1 | `AuctionManager` | ADMIN, ORGANIZER, USER |
| 2 | `ProjectRegistry` | ADMIN, ORGANIZER |
| 3 | `UniversityToken` | ADMIN, ORGANIZER, USER |

**Пример вывода:**

```
🌐 Подключено к сети: http://127.0.0.1:8541
📜 Контракт [ProjectRegistry]: 0x...
🔎 Проверяю адрес: 0xCf3E...
--------------------------------------------------
👑 Роль ADMIN (DEFAULT_ADMIN_ROLE):  ❌ НЕТ
👨‍🏫 Роль TEACHER (ORGANIZER_ROLE):  ✅ ДА
🎓 Роль STUDENT (USER_ROLE):       ❌ НЕТ
```

---

### `get_token_balance.py` — баланс ERC-1155 (`balanceOf`)

Запрашивает on-chain баланс токенов проекта для кошелька.

```bash
cd backend
venv\Scripts\activate

# Интерактивный режим
python scripts/get_token_balance.py

# С аргументами: адрес + blockchain project ID
python scripts/get_token_balance.py 0xCf3EE4870EC092cD1F28291AB6cd8fDbD0EBBB25 1
```

**Пример вывода:**

```
🌐 Сеть: http://127.0.0.1:8541
🪙 Контракт токена (ERC-1155): 0x...
🔎 Проверяемый кошелек: 0xCf3E...
📚 ID Проекта (Token ID): 1
------------------------------------------------------------
📊 Текущий баланс токенов в блокчейне: 💰 1000 UT
```

> `project_id` — это **blockchain ID** проекта (token ID в ERC-1155), а не UUID из PostgreSQL.

---

## 📖 Документация API

### Swagger UI

1. Запустите backend (см. Шаг 5)
2. Откройте **[http://localhost:8000/docs](http://localhost:8000/docs)**
3. Изучите эндпоинты: `/api/v1/auth/`, `/api/v1/projects/`, `/api/v1/auctions/`, `/api/v1/admin/`

### Авторизация через кнопку **Authorize**

1. Зарегистрируйтесь: `POST /api/v1/auth/register`
2. Войдите: `POST /api/v1/auth/login` — получите `access_token` и `refresh_token`
3. Нажмите **Authorize** (🔒) в правом верхнем углу Swagger
4. В поле **Value** введите:

   ```
   Bearer <ваш_access_token>
   ```

   *(слово `Bearer` и пробел обязательны)*

5. Нажмите **Authorize** → **Close**
6. Теперь защищённые эндпоинты (🔒) можно вызывать через **Try it out**

**Обновление токена:**

```
POST /api/v1/auth/refresh
Body: { "refresh_token": "<refresh_token>" }
```

**Выход:**

```
POST /api/v1/auth/logout
Body: { "refresh_token": "<refresh_token>" }
```

---

## 📁 Структура репозитория

```
dapp/
├── infra/                  # PoA-сеть, Docker Compose, genesis, setup.py
├── smartcontracts/         # Solidity, Hardhat, deployed.json, artifacts/
├── backend/                # FastAPI, Alembic, CLI-скрипты
│   ├── app/
│   │   ├── api/            # HTTP-ручки
│   │   ├── services/       # Бизнес-логика
│   │   ├── schemas/        # Pydantic-модели
│   │   ├── models/         # SQLAlchemy ORM
│   │   └── core/           # Config, security, blockchain, crypto
│   ├── alembic/            # Миграции БД
│   └── scripts/            # check_roles.py, get_token_balance.py
└── frontend/               # (в разработке) Next.js UI
```

---

## 📄 Лицензия

Уточняется. См. файл `LICENSE` в корне репозитория.
