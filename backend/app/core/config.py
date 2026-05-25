"""
Модуль, загружающий настройки из .env файла и, позволяющий использовать их
в проекте.
"""

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# получаем абсолютный путь до файла и поднимаемся на 3 уровня выше
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_DIR.parent
INFRA_ENV_FILE = PROJECT_ROOT / "infra" / ".env"


# для установки сопоставления переменных из .env с переменными в коде
class Settings(BaseSettings):
    """Настройки приложения. По умолчанию читает infra/.env (docker-compose)."""

    # Конфигурационная переменная Pydantic для изменения поведения самого класса настроек.
    model_config = SettingsConfigDict(
        env_file=INFRA_ENV_FILE if INFRA_ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore", # игнор любых иных переменных внутри .env
    )

    # дефолтные значения, если их нет в .env
    db_user: str = "dev"
    db_password: str = "devpass_secure_123"
    db_name: str = "unidapp"
    db_host: str = "127.0.0.1"
    db_port: int = 5433

    # Опционально: полный URL (перекрывает отдельные поля)
    # если в .env есть такая строка, то она сраз сюда запишется
    database_url: str | None = None

    # Базовые настройки самого приложения FastAPI (название и флаг режима отладки).
    app_name: str = "UniDApp API"
    debug: bool = False

    def _credentials(self) -> str:
        """Возвращает URL-строку для подключения к БД"""
        # экранирование логина и пароля для вставки в URL-адрес
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def sync_database_url(self) -> str:
        """URL для Alembic (синхронный драйвер psycopg2)."""
        if self.database_url:
            url = self.database_url
            if "+asyncpg" in url:
                # если передаётся асинхронный драйвер, заменяем
                # его на синхронный
                return url.replace("+asyncpg", "+psycopg2", 1)
            if url.startswith("postgresql://"):
                # явно прописываем синхронный драйвер
                return url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return f"postgresql+psycopg2://{self._credentials()}"

    @property
    def async_database_url(self) -> str:
        """URL для FastAPI / SQLAlchemy async (asyncpg)."""
        if self.database_url:
            url = self.database_url
            if "+asyncpg" in url:
                return url
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            if "+psycopg2" in url:
                return url.replace("+psycopg2", "+asyncpg", 1)
            return url
        return f"postgresql+asyncpg://{self._credentials()}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
