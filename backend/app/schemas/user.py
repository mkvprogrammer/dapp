"""
Pydantic-схемы профиля, балансов и активности пользователя.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserStatsResponse(BaseModel):
    """Агрегированная статистика пользователя."""

    won_auctions: int = Field(..., description="Число выигранных аукционов")
    auction_participations: int = Field(..., description="Всего участий в аукционах")
    tokens_earned: Decimal = Field(..., description="Заработано токенов (резерв)")
    confirmed_attendance_hours: Decimal = Field(..., description="Подтверждённые посещения")


class UserProfileResponse(BaseModel):
    """Полный профиль текущего пользователя со статистикой."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(validation_alias="id", description="UUID пользователя")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    faculty: str | None = Field(None, description="Факультет")
    wallet_address: str = Field(..., description="Адрес кошелька")
    role: str = Field(..., description="Роль в системе")
    stats: UserStatsResponse = Field(..., description="Статистика активности")
    created_at: datetime = Field(..., description="Дата регистрации")

    @field_validator("role", mode="before")
    @classmethod
    def _role_str(cls, v):
        return v.value if hasattr(v, "value") else v


class UserProfileUpdate(BaseModel):
    """Частичное обновление профиля (PATCH)."""

    full_name: str | None = Field(None, min_length=2, max_length=150, description="Новое ФИО")
    faculty: str | None = Field(None, max_length=200, description="Факультет")


class ProjectBalanceItem(BaseModel):
    """Баланс токенов пользователя в одном проекте."""

    project_id: int = Field(..., description="ID проекта")
    project_name: str = Field(..., description="Название проекта")
    available: Decimal = Field(..., description="Доступно onchain")
    frozen: Decimal = Field(..., description="Заморожено в активных ставках")
    pending_refund: Decimal = Field(..., description="Ожидаемый возврат")


class UserBalancesResponse(BaseModel):
    """Сводный баланс по всем проектам пользователя."""

    total: Decimal = Field(..., description="Сумма available + frozen")
    available: Decimal = Field(..., description="Доступно к трате")
    frozen: Decimal = Field(..., description="В ставках")
    pending_refund: Decimal = Field(..., description="Ожидаемые возвраты")
    by_project: list[ProjectBalanceItem] = Field(..., description="Разбивка по проектам")


class ActivityItem(BaseModel):
    """Элемент ленты активности."""

    id: UUID = Field(..., description="ID события")
    type: str = Field(..., description="Тип: auction_bid, transfer_in, transfer_out")
    title: str = Field(..., description="Заголовок")
    description: str = Field(..., description="Краткое описание")
    project_id: int | None = Field(None, description="Связанный проект")
    project_name: str | None = Field(None, description="Название проекта")
    amount_delta: Decimal | None = Field(None, description="Изменение баланса (+/-)")
    created_at: datetime = Field(..., description="Время события")


class ActivityListResponse(BaseModel):
    """Пагинированная лента активности."""

    items: list[ActivityItem] = Field(..., description="События")
    total: int = Field(..., description="Общее число событий в выборке")


class MyActiveAuctionItem(BaseModel):
    """Активный аукцион, в котором участвует пользователь."""

    auction_id: int = Field(..., description="ID аукциона")
    project_id: int = Field(..., description="ID проекта")
    resource_name: str = Field(..., description="Название ресурса")
    project_name: str = Field(..., description="Название проекта")
    my_bid_amount: Decimal = Field(..., description="Сумма текущей ставки")
    my_rank: int = Field(..., description="Позиция в лидерборде")
    participants_count: int = Field(..., description="Число участников")
    end_time: datetime = Field(..., description="Окончание торгов")
    time_left_seconds: int = Field(..., description="Секунд до конца торгов")


class MyActiveAuctionsResponse(BaseModel):
    """Список активных аукционов с ставкой пользователя."""

    items: list[MyActiveAuctionItem] = Field(..., description="Аукционы")
