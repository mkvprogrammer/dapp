"""
Pydantic-схемы для аукционов и ставок.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuctionCreate(BaseModel):
    """Тело запроса на создание аукциона."""

    project_id: int = Field(..., description="ID проекта в БД")
    resource_name: str = Field(..., min_length=3, max_length=150, description="Название ресурса")
    duration_seconds: int = Field(..., gt=0, description="Длительность торгов в секундах")
    lesson_start_time: datetime = Field(..., description="Время начала занятия (UTC)")
    resource_limit: int = Field(..., gt=0, description="Число гарантированных мест")
    password: str = Field(..., description="Пароль создателя для подписи транзакции")
    resource_type: str = Field(default="consultation", max_length=32, description="Тип ресурса")
    location: str | None = Field(None, max_length=200, description="Место проведения")
    description: str | None = Field(None, description="Описание аукциона")
    min_bid: Decimal = Field(default=Decimal("1"), gt=0, description="Минимальная ставка")
    bid_step: Decimal = Field(default=Decimal("1"), gt=0, description="Шаг повышения ставки")
    image_url: str | None = Field(None, max_length=500, description="URL изображения")


def _enum_to_str(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return value.value
    return value


class AuctionListResponse(BaseModel):
    """Краткая карточка аукциона в списке."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID аукциона")
    project_id: int = Field(..., description="ID проекта")
    resource_name: str = Field(..., description="Название ресурса")
    resource_limit: int = Field(..., description="Лимит мест")
    status: str = Field(..., description="open, closed, cancelled")

    @field_validator("status", mode="before")
    @classmethod
    def _status_as_str(cls, value: str | Enum) -> str:
        return _enum_to_str(value)


class AuctionDetailResponse(BaseModel):
    """Полные детали аукциона."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID аукциона")
    project_id: int = Field(..., description="ID проекта")
    resource_name: str = Field(..., description="Название ресурса")
    start_time: datetime = Field(..., description="Начало торгов")
    end_time: datetime = Field(..., description="Окончание торгов")
    lesson_start_time: datetime = Field(..., description="Начало занятия")
    resource_limit: int = Field(..., description="Гарантированных мест")
    blockchain_auction_id: int = Field(..., description="ID в AuctionManager")
    status: str = Field(..., description="Статус аукциона")
    resource_type: str | None = Field(None, description="Тип ресурса")
    location: str | None = Field(None, description="Место")
    description: str | None = Field(None, description="Описание")
    min_bid: Decimal | None = Field(None, description="Минимальная ставка")
    bid_step: Decimal | None = Field(None, description="Шаг ставки")
    image_url: str | None = Field(None, description="URL изображения")
    created_at: datetime = Field(..., description="Дата создания")

    @field_validator("status", mode="before")
    @classmethod
    def _status_as_str(cls, value: str | Enum) -> str:
        return _enum_to_str(value)


class AuctionCreatedResponse(BaseModel):
    """Ответ после создания аукциона."""

    id: int = Field(..., description="ID аукциона в БД")
    resource_name: str = Field(..., description="Название ресурса")
    blockchain_auction_id: int = Field(..., description="ID onchain")
    tx_hash: str = Field(..., description="Хэш транзакции создания")


class BidCreate(BaseModel):
    """Тело запроса на размещение или повышение ставки."""

    amount: Decimal = Field(..., gt=0, description="Сумма ставки (или дополнение)")
    password: str = Field(..., description="Пароль студента для approve/placeBid")


class BidCancelRequest(BaseModel):
    """Тело запроса на отмену ставки."""

    password: str = Field(..., description="Пароль студента для подписи cancelBid")


class BidResponse(BaseModel):
    """Результат размещения ставки."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="ID ставки")
    auction_id: int = Field(..., description="ID аукциона")
    user_id: UUID = Field(..., description="ID студента")
    amount: Decimal = Field(..., description="Итоговая сумма ставки")
    status: str = Field(..., description="Статус: locked, refunded и др.")
    tx_hash: str = Field(..., description="Хэш onchain-транзакции")


class LeaderboardEntry(BaseModel):
    """Участник лидерборда аукциона."""

    wallet_address: str = Field(..., description="Адрес кошелька")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    amount: Decimal = Field(..., description="Сумма ставки")
    is_guaranteed: bool = Field(..., description="Входит в топ resource_limit")


class LeaderboardResponse(BaseModel):
    """Лидерборд ставок аукциона."""

    auction_id: int = Field(..., description="ID аукциона")
    entries: list[LeaderboardEntry] = Field(..., description="Участники по убыванию ставки")


class CancelBidResponse(BaseModel):
    """Ответ после отмены ставки."""

    auction_id: int = Field(..., description="ID аукциона")
    status: str = Field(..., description="Новый статус ставки")
    tx_hash: str = Field(..., description="Хэш onchain-транзакции")


class AuctionListResponseExtended(BaseModel):
    """Расширенная карточка аукциона для списка с агрегатами."""

    id: int = Field(..., description="ID аукциона")
    project_id: int = Field(..., description="ID проекта")
    project_name: str = Field(..., description="Название проекта")
    resource_name: str = Field(..., description="Название ресурса")
    resource_limit: int = Field(..., description="Лимит мест")
    status: str = Field(..., description="Статус")
    start_time: datetime | None = Field(None, description="Начало торгов")
    end_time: datetime | None = Field(None, description="Окончание торгов")
    current_top_bid: Decimal | None = Field(None, description="Максимальная ставка")
    participants_count: int = Field(0, description="Число участников")
    my_bid_amount: Decimal | None = Field(None, description="Ставка текущего пользователя")
    my_rank: int | None = Field(None, description="Ранг текущего пользователя")
    image_url: str | None = Field(None, description="URL изображения")


class BidHistoryEntry(BaseModel):
    """Событие в истории ставок."""

    id: UUID = Field(..., description="ID события")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    amount: Decimal = Field(..., description="Сумма операции")
    action: str = Field(..., description="placed, raised, cancelled")
    created_at: datetime = Field(..., description="Время события")


class BidHistoryResponse(BaseModel):
    """История событий ставок по аукциону."""

    auction_id: int = Field(..., description="ID аукциона")
    entries: list[BidHistoryEntry] = Field(..., description="События в хронологическом порядке")
