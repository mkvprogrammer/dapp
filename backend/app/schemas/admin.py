"""
Схемы панели администратора.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.user import UserRole


class ChangeRoleRequest(BaseModel):
    """Запрос на смену роли пользователя."""

    new_role: UserRole = Field(..., description="Новая роль: admin, organizer, student")


class AdminUserListItem(BaseModel):
    """Элемент списка пользователей в админ-панели."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(validation_alias="id", description="UUID пользователя")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    wallet_address: str = Field(..., description="Адрес кошелька")
    role: str = Field(..., description="Текущая роль")
    is_active: bool = Field(..., description="Активен ли аккаунт")
    last_login_at: datetime | None = Field(None, description="Время последнего входа")
    created_at: datetime = Field(..., description="Дата регистрации")

    @field_validator("role", mode="before")
    @classmethod
    def _role_as_str(cls, value: str | Enum) -> str:
        if isinstance(value, Enum):
            return value.value
        return value


class AdminUserListResponse(BaseModel):
    """Пагинированный список пользователей."""

    items: list[AdminUserListItem] = Field(..., description="Страница результатов")
    total: int = Field(..., description="Общее число записей по фильтру")


class AuditLogEntry(BaseModel):
    """Запись журнала аудита."""

    id: UUID = Field(..., description="ID записи")
    created_at: datetime = Field(..., description="Время события")
    actor_name: str = Field(..., description="ФИО инициатора или «Система»")
    actor_student_id: str | None = Field(None, description="ID студента инициатора")
    action: str = Field(..., description="Код действия")
    object_ref: str = Field(..., description="Ссылка на объект (user:, auction: и т.д.)")
    ip_address: str | None = Field(None, description="IP-адрес клиента")


class AuditLogResponse(BaseModel):
    """Пагинированный журнал аудита."""

    items: list[AuditLogEntry] = Field(..., description="Записи журнала")
    total: int = Field(..., description="Общее число записей")


class EmergencyStopRequest(BaseModel):
    """Запрос экстренной остановки аукционов."""

    reason: str = Field(..., min_length=10, max_length=500, description="Причина остановки для audit log")


class EmergencyStopResponse(BaseModel):
    """Результат экстренной остановки."""

    stopped_auctions_count: int = Field(..., description="Число отменённых аукционов в БД")
    message: str = Field(..., description="Сообщение для оператора")


class ServiceHealth(BaseModel):
    """Состояние одного компонента инфраструктуры."""

    name: str = Field(..., description="Имя сервиса (PostgreSQL, Blockchain)")
    status: str = Field(..., description="ok или error")
    detail: str = Field(..., description="Детали проверки")
    latency_ms: int | None = Field(None, description="Задержка ответа в мс")


class AdminHealthResponse(BaseModel):
    """Сводка здоровья системы для админ-панели."""

    services: list[ServiceHealth] = Field(..., description="Статус зависимостей")
    active_auctions: int = Field(..., description="Число открытых аукционов")
    bids_per_hour: int = Field(..., description="Ставок за последний час")
    blockchain_block_number: int | None = Field(None, description="Номер последнего блока PoA")
