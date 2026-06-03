# Недостающие API для полного соответствия вёрстке

> **Полная спецификация со схемами Pydantic:** [`backend/docs/API_GAP.md`](../backend/docs/API_GAP.md)

React-приложение подключено к существующим эндпоинтам `/api/v1`. Ниже — краткая сводка.

## Уже реализовано (используется во фронтенде)

| Область | Эндпоинты |
|---------|-----------|
| Auth | `POST /auth/register`, `login`, `logout`, `refresh`, `GET /auth/me` |
| Projects | `GET /projects/`, `GET /projects/{id}`, `POST /projects/`, `POST /projects/{id}/enroll` |
| Auctions | `GET /auctions/`, `GET /auctions/{id}`, `GET /auctions/{id}/leaderboard`, `POST /auctions/`, `POST /auctions/{id}/bid`, `DELETE /auctions/{id}/bid` |
| Admin | `PUT /admin/users/{user_id}/role` |
| Система | `GET /health` (базовый статус БД) |

## Не хватает для полного функционала макетов

### Dashboard / главная (`home.html`)

- `GET /dashboard` или агрегат: общий баланс TKN, число непрочитанных уведомлений, выигрыши за месяц, превью активности
- `GET /users/me/balances` — баланс по проектам и суммарный

### Профиль (`profile.html`)

- `GET /users/me/profile` — email, факультет, статистика (победы, участия, часы посещений)
- `PATCH /users/me/profile` — редактирование
- `GET /users/me/activity` — лента событий
- `GET /users/me/auctions/active` — активные аукционы пользователя с рангом и ставкой

### Проекты (`projects.html`, `project-details.html`)

- `GET /users/me/projects` — только проекты, где пользователь записан (сейчас `GET /projects/` — все проекты)
- `GET /projects/{id}/members` — список участников
- `GET /projects/{id}/balance` — баланс текущего пользователя в проекте
- `POST /projects/join-by-code` — «Присоединиться» по коду (в макете кнопка без ID)
- Фильтры: архив, сортировка, поиск — query-параметры к списку

### Посещения / коды (`project-details`, `organizer.html`)

- `POST /projects/{id}/attendance-codes` — генерация кода
- `GET /projects/{id}/attendance-codes/active`
- `POST /projects/{id}/attendance/redeem` — ввод кода студентом
- `GET /projects/{id}/attendance/stats` — процент посещаемости

### Организатор (`organizer.html`)

- `GET /projects/{id}/organizer/stats` — участники, токены в обороте, графики
- `POST /projects/{id}/members/{user_id}/mint-tokens` — начисление токенов
- `GET /projects/{id}/members` — таблица участников с балансом и посещениями

### Переводы (`transfers.html`)

- `GET /wallet/balance` или баланс в рамках проекта
- `POST /transfers` — `{ recipient_student_id, amount, comment?, project_id? }`
- `GET /transfers` — история с пагинацией
- `GET /transfers/recent-recipients`
- `GET /transfers/export?format=csv`

### Уведомления (`notifications.html`)

- `GET /notifications?type=&unread_only=`
- `PATCH /notifications/{id}/read`
- `PATCH /notifications/read-all`

### Аукционы — расширение макета (`auctions.html`, `create-auction.html`, `auction-details.html`)

- Query для `GET /auctions/`: `project_id`, `status`, `search`
- Поля в ответе: `current_top_bid`, `participants_count`, `end_time` в списке
- `GET /auctions/{id}/bid-history` — история ставок с временем (сейчас только leaderboard)
- Расширение `POST /auctions/`: `location`, `resource_type`, `min_bid`, `bid_step`, `image_url`, черновики
- WebSocket или SSE для live-обновления рейтинга и таймера

### Админ (`admin.html`)

- `GET /admin/users` — список с поиском, ролями, последним входом
- `GET /admin/audit-log?event_type=`
- `POST /admin/emergency-stop`
- `GET /admin/health` — детальный статус (очередь, blockchain node)

### Прочее

- `POST /wallet/top-up` — «Пополнить» / «Получить TKN» в макете
- Загрузка файлов (изображение аукциона)
- Документация — статический контент, API не нужен

## Расхождение полей UI ↔ backend

| Макет | Backend |
|-------|---------|
| ITMO ID | `student_id` |
| Название аукциона + тип + место | только `resource_name` |
| Несколько дат (auction-start/end) | `duration_seconds` + `lesson_start_time` |
| Мин. ставка / шаг ставки | не в схеме; ставка только `amount` в bid |

## Запуск

```bash
# Backend (из корня infra + backend)
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

Vite проксирует `/api` и `/health` на `http://localhost:8000`. CORS настроен для `localhost:5173`.
