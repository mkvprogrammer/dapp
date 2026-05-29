from collections.abc import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Именование ограничений для Alembic autogenerate
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


# Создает единый родительский класс Base для всех будущих таблиц проекта
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=convention)


# создает пул асинхронных соединений с БД
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
)

# Создает фабрику-генератор сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,  # указание, что сессии должны работать в асинхронном режиме
    expire_on_commit=False,
)


# открывает сессию связи с БД для каждого входящего HTTP-запроса в FastAPI 
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        # Функция отдает открытую сессию в эндпоинт FastAPI, ждет, 
        # пока этот эндпоинт выполнит свою логику (например, запишет ставку в БД),
        # а затем управление возвращается обратно сюда, чтобы 
        # контекстный менеджер закрыл сессию
        yield session
