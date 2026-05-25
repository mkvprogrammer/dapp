import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Корень backend — в sys.path для импорта app.* и database
_backend_dir = Path(__file__).resolve().parents[1]
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.core.config import settings  # noqa: E402
from database import Base  # noqa: E402

# Извлекает объект конфигурации из файла alembic.ini
config = context.config

# Настройка логирования, для вывода сообщений от Alembic в консоль
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# передаем Alembic слепок (metadata) всех наших ORM-моделей
# чтобы Alembic знал, какие таблицы мы создали в коде
target_metadata = Base.metadata


def _get_url() -> str:
    """Получение синхронной URL для работы с БД"""
    return settings.sync_database_url


def run_migrations_offline() -> None:
    """Миграции без подключения к БД (генерация SQL-скрипта)."""
    context.configure(
        url=_get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Миграции с живым подключением к PostgreSQL из docker-compose."""
    config.set_main_option("sqlalchemy.url", _get_url())

    # синхронный движок для работы с БД
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool, # отключает кэширование соединений (т.к миграция - разовая задача)
    )

    with connectable.connect() as connection:
        # настрйока конткекста Alembic перед запуском миграции
        # куда отправлять, что отправлять (+ в начале сравнить с уже имеющимся состоянием)
        context.configure(connection=connection, target_metadata=target_metadata)

        # применение изменений
        with context.begin_transaction():
            context.run_migrations()


# точка входа; определяет режим выполнения скрипта в зависимости
# от флага запуска
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
