"""
Зависимости FastAPI: аутентификация и доступ к текущему пользователю.
"""

from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.models.user import User, UserRole
from database import get_db

# Схема Bearer для Swagger; tokenUrl — только для документации OpenAPI
# создает специальный служебный объект, который отвечает за автоматический поиск,
# извлечение и валидацию формата JWT-токена из входящих HTTP-запросов
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Извлекает и проверяет access-токен, возвращает активного пользователя из БД.
    Добавляя данную зависимость в ручку, мы автоматически делаем ручку защищённой, 
    так как для доступа к ней потребуется передавать JWT-токен пользователя.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # проверка валидности токена
        payload = decode_access_token(token)
        user_id = UUID(str(payload["sub"]))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise credentials_exc from None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        """Фабрика принимает список ролей, которым разрешен доступ."""
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """
        Метод срабатывает автоматически, когда мы пишем Depends(RoleChecker(...)).
        Он берет пользователя из get_current_user и сверяет его роль.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have enough permissions to perform this action",
            )
        # Если роль совпала — возвращаем пользователя дальше в ручку
        return current_user
