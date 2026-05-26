"""
Pydantic-схемы валидации для эндпоинтов авторизации.
"""

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserRegister(BaseModel):
    student_id: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    student_id: str
    password: str


class LogoutRequest(BaseModel):
    """Схема для запроса выхода из системы."""
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    # Если тебе подсунут ORM-модель, читай её поля как атрибуты объекта через точку
    # нужно так как по умолчанию Pydantic работает только со словарями Python
    model_config = ConfigDict(from_attributes=True)

    # ищи поле с именем id, но в итоговый JSON
    # запиши значение этого поля в поле с именем user_id
    user_id: UUID = Field(validation_alias="id")
    student_id: str
    full_name: str
    wallet_address: str
    role: str

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
    """Схема ответа строго для регистрации. Отдает приватный ключ один раз."""
    private_key: str
