"""
Pydantic-схемы in-app уведомлений.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationMeta(BaseModel):
    """Дополнительные данные уведомления (контекст для UI)."""

    project_id: int | None = Field(None, description="Связанный проект")
    project_name: str | None = Field(None, description="Название проекта")
    auction_id: int | None = Field(None, description="Связанный аукцион")
    bid_amount: Decimal | None = Field(None, description="Сумма ставки")
    rank: int | None = Field(None, description="Позиция в лидерборде")
    balance_after: Decimal | None = Field(None, description="Баланс после операции")
    action_url: str | None = Field(None, description="Ссылка для перехода в UI")


class NotificationItem(BaseModel):
    """Одно уведомление пользователя."""

    id: UUID = Field(..., description="ID уведомления")
    type: str = Field(..., description="Тип: bid_outbid, transfer_received и др.")
    title: str = Field(..., description="Заголовок")
    body: str = Field(..., description="Текст уведомления")
    meta: dict = Field(..., description="Произвольные метаданные")
    is_read: bool = Field(..., description="Прочитано ли")
    created_at: datetime = Field(..., description="Время создания")


class NotificationListResponse(BaseModel):
    """Пагинированный список уведомлений."""

    items: list[NotificationItem] = Field(..., description="Уведомления")
    total: int = Field(..., description="Всего по фильтру")
    unread_count: int = Field(..., description="Непрочитанных (глобально)")


class NotificationReadResponse(BaseModel):
    """Ответ после пометки одного уведомления прочитанным."""

    id: UUID = Field(..., description="ID уведомления")
    is_read: bool = Field(..., description="Статус прочтения")


class NotificationReadAllResponse(BaseModel):
    """Ответ после массовой пометки прочитанными."""

    updated_count: int = Field(..., description="Число обновлённых записей")
