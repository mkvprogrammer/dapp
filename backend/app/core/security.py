"""
Модуль безопасности: хэширование паролей и выпуск JWT-токенов.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings

# Контекст bcrypt для хэширования паролей (соль генерируется автоматически)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM: str = settings.algorithm


def get_password_hash(password: str) -> str:
    """Хэширует сырой пароль с солью (bcrypt)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие сырого пароля хэшу из БД."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Генерирует короткоживущий JWT access-токен.

    В payload ожидаются как минимум ``sub`` (ID пользователя) и ``role``.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Генерирует долгоживущий JWT refresh-токен (по умолчанию 7 дней).

    В payload ожидаются как минимум ``sub`` и ``role``.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=ALGORITHM,
    )
