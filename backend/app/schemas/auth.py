"""
Pydantic-схемы валидации для эндпоинтов авторизации.
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    """Тело запроса регистрации нового студента."""

    student_id: str = Field(..., min_length=3, max_length=50, description="Уникальный ID студента (логин)")
    full_name: str = Field(..., min_length=2, max_length=150, description="ФИО пользователя")
    password: str = Field(..., min_length=8, description="Пароль для входа и шифрования кошелька")


class UserLogin(BaseModel):
    """Тело запроса входа в систему."""

    student_id: str = Field(..., description="ID студента")
    password: str = Field(..., description="Пароль")


class LogoutRequest(BaseModel):
    """Схема для запроса выхода из системы."""

    refresh_token: str = Field(..., description="Refresh-токен, подлежащий отзыву")


class TokenResponse(BaseModel):
    """Пара JWT-токенов после входа или обновления сессии."""

    access_token: str = Field(..., description="Краткоживущий access-токен (Bearer)")
    refresh_token: str = Field(..., description="Долгоживущий refresh-токен для ротации")
    token_type: str = Field(default="bearer", description="Тип токена для заголовка Authorization")


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление access-токена по refresh-токену."""

    refresh_token: str = Field(..., description="Действующий refresh-токен")


class UserResponse(BaseModel):
    """Публичный профиль пользователя (без секретов)."""

    # Если тебе подсунут ORM-модель, читай её поля как атрибуты объекта через точку
    # нужно так как по умолчанию Pydantic работает только со словарями Python
    model_config = ConfigDict(from_attributes=True)

    # ищи поле с именем id, но в итоговый JSON
    # запиши значение этого поля в поле с именем user_id
    user_id: UUID = Field(validation_alias="id", description="UUID пользователя в БД")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    wallet_address: str = Field(..., description="Ethereum-адрес кошелька")
    role: str = Field(..., description="Роль: admin, organizer, student")

    # перехватывает значение поля role до того, как Pydantic начнет проверять его тип
    @field_validator("role", mode="before")
    @classmethod
    def _role_as_str(cls, value: str | Enum) -> str:
        """
        если из базы прилетел полноценный объект Enum,
        она забирает из него чистую строку через свойство .value
        """
        if isinstance(value, Enum):
            return value.value
        return value


class UserRegisterResponse(UserResponse):
    """Ответ регистрации: профиль + одноразовая выдача приватного ключа кошелька."""

    private_key: str = Field(..., description="Сырой приватный ключ (сохранить клиенту один раз)")
