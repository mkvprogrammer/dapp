# Статус API и UI

> Спецификация: [`backend/docs/API_GAP.md`](../backend/docs/API_GAP.md)

## Реализовано

| Область | Backend | Frontend |
|---------|---------|----------|
| Auth | register, login, logout, refresh, me | Login, Register |
| Dashboard | агрегат + recent_activity | HomePage |
| Users | profile, PATCH profile, balances, activity, projects | ProfilePage |
| Projects | CRUD, enroll, join-by-code, members, mint, balance, stats | Projects, ProjectDetails, Organizer |
| Auctions | list, detail, create, bid, leaderboard, bid-history, attendance | Auctions, Details, Create |
| Transfers | create, list, recent-recipients, export CSV | TransfersPage |
| Notifications | list, read, read-all + события в сервисах | NotificationsPage, badge в Topbar |
| Wallet | balance, demo-top-up | — (debug API) |
| Admin | users, audit-log, emergency, health, roles | AdminPage |
| Uploads | POST images | CreateAuction |
| Celery | закрытие аукционов + уведомления участникам | — |

**Намеренно не в scope:** коды посещения, email в профиле.

## Оставшиеся упрощения

- Emergency stop — только БД, без onchain
- SSE `/auctions/{id}/stream` — на UI опрос лидерборда 5 с (EventSource без Bearer в браузере)
- Автотесты `pytest` — не добавлены
- Индексация событий блокчейна в Celery — не реализована

## Запуск

```bash
cd backend && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

Vite проксирует `/api` и `/health` на `http://localhost:8000`.
