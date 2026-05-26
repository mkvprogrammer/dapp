"""
HTTP-ручки авторизации (тонкий слой над app.services.auth).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    UserRegisterResponse,
    LogoutRequest
)
from app.services import auth as auth_service
from app.models.user import User
from app.api.dependencies import get_current_user
from database import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> UserRegisterResponse:
    """Регистрация нового студента."""
    user, raw_private_key = await auth_service.register_user(db, payload)
    return UserRegisterResponse(
        id=user.id, # передаем именно id=user.id, так как validation_alias требует имя "id"
        student_id=user.student_id,
        full_name=user.full_name,
        wallet_address=user.wallet_address,
        role=user.role.value, # Передаем чистую строку из Enum
        private_key=raw_private_key
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Вход: проверка учётных данных и выдача пары JWT."""
    user = await auth_service.authenticate_user(db, payload)
    tokens = await auth_service.create_jwt_tokens(db, user)
    return TokenResponse(**tokens)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Защищаем ручку: проверяем access_token
):
    """
    Выход из системы. Аннулирует переданный refresh-токен.
    Требует передачи валидного Access Token в заголовке Authorization.
    """
    # Вызываем сервис для отзыва токена
    await auth_service.logout_user(db, payload.refresh_token)
    
    # Фронтенд, получив этот ответ, должен сам стереть оба токена из своей памяти
    return {"detail": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Ротация refresh-токена и выпуск новой пары JWT."""
    new_tokens = await auth_service.refresh_access_token(db, payload.refresh_token)
    return TokenResponse(**new_tokens)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user) # Зависимость сама всё проверит
) -> UserResponse:
    """
    Получение профиля текущего авторизованного пользователя.
    Доступно любому пользователю с валидным Access Token.
    """
    # Просто возвращаем объект. Pydantic-модель UserResponse сама 
    # отфильтрует password_hash и красиво преобразует типы данных.
    return current_user
