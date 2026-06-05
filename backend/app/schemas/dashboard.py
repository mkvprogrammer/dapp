"""
Pydantic-схемы главной страницы (дашборд).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardProjectPreview(BaseModel):
    """Краткая карточка проекта на главной."""

    project_id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название")
    token_balance: Decimal = Field(..., description="Доступный баланс токенов")
    active_auctions_count: int = Field(..., description="Открытых аукционов в проекте")
    activity_percent: int = Field(..., ge=0, le=100, description="Условная активность 0–100%")


class DashboardAuctionPreview(BaseModel):
    """Краткая карточка аукциона на главной."""

    auction_id: int = Field(..., description="ID аукциона")
    resource_name: str = Field(..., description="Название ресурса")
    project_id: int = Field(..., description="ID проекта")
    project_name: str = Field(..., description="Название проекта")
    status: str = Field(..., description="Статус аукциона")
    my_bid_amount: Decimal | None = Field(None, description="Моя ставка")
    my_rank: int | None = Field(None, description="Мой ранг")
    participants_count: int = Field(..., description="Число участников")
    end_time: datetime = Field(..., description="Окончание торгов")
    image_url: str | None = Field(None, description="URL изображения")


class DashboardActivityPreview(BaseModel):
    """Сокращённый элемент ленты активности на главной."""

    id: UUID = Field(..., description="ID события")
    type: str = Field(..., description="Тип события")
    title: str = Field(..., description="Заголовок")
    description: str = Field(..., description="Описание")
    amount_delta: Decimal | None = Field(None, description="Изменение баланса")
    created_at: datetime = Field(..., description="Время")


class DashboardResponse(BaseModel):
    """Агрегированные данные главной страницы."""

    total_balance: Decimal = Field(..., description="Суммарный баланс токенов")
    active_auctions_count: int = Field(..., description="Активных аукционов у пользователя")
    projects_count: int = Field(..., description="Число проектов")
    wins_this_month: int = Field(..., description="Подтверждённых посещений за месяц")
    unread_notifications_count: int = Field(..., description="Непрочитанных уведомлений")
    projects: list[DashboardProjectPreview] = Field(..., description="Проекты пользователя")
    active_auctions: list[DashboardAuctionPreview] = Field(..., description="Топ активных аукционов")
    recent_activity: list[DashboardActivityPreview] = Field(..., description="Последние события")
