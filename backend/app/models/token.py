"""
Отвечает за хранение Refresh токенов
"""
from __future__ import annotations # воспринимает аннотации как строки 
                                   # для избежания ошибок с импортами

from typing import TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base # Ваш базовый класс

# Этот блок выполняется ТОЛЬКО во время проверки типов вашей IDE (VS Code/PyCharm).
# В рантайме (при запуске) Python этот импорт полностью игнорирует, что исключает циклическую ошибку!
if TYPE_CHECKING:
    from .user import User 


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    # Поля по умолчанию NOT NULL, nullable=False писать больше не нужно
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Обратная связь к пользователю
    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")
