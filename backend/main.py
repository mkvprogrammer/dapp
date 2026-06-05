import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.api import api_router
from app.core.config import get_settings, settings
from app.core.exceptions import DomainException
from app.core.handlers import (
    domain_exception_handler,
    request_validation_exception_handler,
)
from database import engine


# механизм FastAPI для выполнения кода до старта сервера и после его остановки.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Проверка подключения к PostgreSQL при старте."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except (OperationalError, OSError) as exc:
        get_settings.cache_clear()
        cfg = get_settings()
        raise RuntimeError(
            f"Не удалось подключиться к PostgreSQL ({cfg.db_host}:{cfg.db_port}). "
            "Убедитесь, что контейнер db запущен: cd infra && docker compose up -d db. "
            "На Windows порт 5432 часто занят локальным PostgreSQL — проект использует 5433. "
            f"Оригинальная ошибка: {exc!r}"
        ) from exc
    yield  # Разделяет логику старта и остановки
    await engine.dispose()


# Создает экземпляр приложения FastAPI, передавая ему имя из настроек
# и регистрируя функцию управления жизненным циклом lifespan
app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальный перехват доменных ошибок (сервисы → HTTP)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(DomainException, domain_exception_handler)

# API v1: /api/v1/auth/...
app.include_router(api_router)

upload_path = Path(settings.upload_dir)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")


@app.get("/")
async def root():
    """Корневой эндпоинт: имя приложения и статус работы."""
    return {"message": settings.app_name, "status": "running"}


@app.get("/health")
async def health():
    """Проверка здоровья API и подключения к PostgreSQL."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=settings.debug,
    )
