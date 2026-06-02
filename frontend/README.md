# AuctionChain — Frontend

React-приложение (JSX) на основе статической вёрстки в `pages/` и `css/`. Стили подключены без изменений.

## Структура

| Путь | Описание |
|------|----------|
| `pages/`, `css/`, `assets/` | Исходные HTML-макеты (референс) |
| `src/` | React: страницы, API-клиент, layout |
| `public/` | Статика для Vite (логотип) |
| `MISSING_API.md` | Эндпоинты, которых не хватает для полного UI |

## Запуск

1. Backend: `cd backend && uvicorn main:app --reload` (порт 8000)
2. Frontend:

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173 — запросы к `/api` проксируются на backend.

## Сборка

```bash
npm run build
npm run preview
```

## Маршруты

- `/login`, `/register` — авторизация
- `/` — главная
- `/profile`, `/projects`, `/projects/:id`
- `/auctions`, `/auctions/:id`, `/create-auction`
- `/transfers`, `/notifications`, `/organizer`
- `/admin` — только роль `admin`
