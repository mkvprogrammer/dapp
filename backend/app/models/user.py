from __future__ import annotations # воспринимает аннотации как строки 
                                   # для избежания ошибок с импортами

import enum
from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base # Ваш базовый класс


# Этот блок выполняется ТОЛЬКО во время проверки типов вашей IDE (VS Code/PyCharm).
# В рантайме (при запуске) Python этот импорт полностью игнорирует, что исключает циклическую ошибку!
if TYPE_CHECKING:
    from .token import RefreshToken # Импорт только для IDE


# Создаем Enum для ролей
class UserRole(str, enum.Enum):
    STUDENT = "student"
    ORGANIZER = "organizer"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    # Аннотация типа (например, UUID) определяет тип колонки в Python,
    # а mapped_column() задает настройки для самой базы данных.
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    
    # String(50) пишется внутри mapped_column, если нужно ограничить длину
    student_id: Mapped[str] = mapped_column(String(50), unique=True)
    full_name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    wallet_address: Mapped[str] = mapped_column(String(42), unique=True)
    
    # По умолчанию поле NOT NULL (nullable=False). Если нужно разрешить NULL,
    # пишется Mapped[str | None]
    # Используем Enum вместо строки. native_enum=False сделает текстовое поле в БД
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False), 
        default=UserRole.STUDENT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # server_default и onupdate работают точно так же
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # Добавили связь с токенами и каскадное удаление - чтобы при удалении
    # пользователя из БД, удалялись все его токены
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
