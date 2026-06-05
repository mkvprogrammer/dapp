"""
Pydantic-схемы для управления проектами.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Создание проекта организатором."""

    name: str = Field(..., min_length=3, max_length=100, description="Название курса/проекта")
    description: str | None = Field(None, description="Описание")
    password: str = Field(..., description="Пароль организатора для расшифровки приватного ключа")
    refund_rate: Decimal = Field(default=Decimal("80.00"), examples=[Decimal("80.00")], description="Процент возврата при посещении")
    penalty_schedule: list[int] = Field(default_factory=lambda: [10, 20, 30, 50], description="Шкала штрафов за прогулы (4 значения)")
    initial_supply: int = Field(default=1000, ge=1, description="Стартовые токены при записи на курс")

    @field_validator("penalty_schedule")
    @classmethod
    def _validate_penalty_schedule(cls, value: list[int]) -> list[int]:
        if len(value) != 4:
            raise ValueError("penalty_schedule must contain exactly 4 values")
        return value


class ProjectListResponse(BaseModel):
    """Краткая карточка проекта в списке."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID проекта (= blockchain_id)")
    name: str = Field(..., description="Название")
    organizer_id: UUID = Field(..., description="UUID организатора")
    is_active: bool = Field(..., description="Активен ли проект")


class ProjectDetailResponse(BaseModel):
    """Полная информация о проекте."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название")
    description: str = Field(..., description="Описание")
    organizer_id: UUID = Field(..., description="UUID организатора")
    blockchain_id: int = Field(..., description="ID в ProjectRegistry")
    refund_rate: Decimal = Field(..., description="Процент возврата")
    penalty_schedule: list[int] = Field(..., description="Шкала штрафов")
    initial_supply: int = Field(..., description="Стартовые токены при enroll")
    is_active: bool = Field(..., description="Активен ли проект")
    join_code: str | None = Field(None, description="Код приглашения для студентов")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")


class ProjectCreatedResponse(BaseModel):
    """Ответ после создания проекта onchain."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название")
    blockchain_id: int = Field(..., description="ID в блокчейне")
    join_code: str | None = Field(None, description="Код для записи студентов")
    tx_hash: str = Field(..., description="Хэш транзакции создания")


class EnrollResponse(BaseModel):
    """Ответ после записи студента на проект."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(..., description="UUID студента")
    project_id: int = Field(..., description="ID проекта")
    enrolled_at: datetime = Field(..., description="Время записи")
    token_balance: Decimal = Field(..., description="Начальный баланс после mint")
    tx_hash: str = Field(..., description="Хэш транзакции mint")


class ProjectMemberResponse(BaseModel):
    """Участник проекта для панели организатора."""

    user_id: UUID = Field(..., description="UUID участника")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    wallet_address: str = Field(..., description="Адрес кошелька")
    token_balance: Decimal = Field(..., description="Onchain-баланс токенов")
    enrolled_at: datetime = Field(..., description="Дата записи")


class MintTokensRequest(BaseModel):
    """Запрос на дополнительный mint токенов участнику."""

    amount: int = Field(..., ge=1, le=1_000_000, description="Количество токенов для начисления")


class MintTokensResponse(BaseModel):
    """Ответ после mint токенов участнику."""

    user_id: UUID = Field(..., description="UUID участника")
    project_id: int = Field(..., description="ID проекта")
    amount: int = Field(..., description="Начисленная сумма")
    new_balance: Decimal = Field(..., description="Новый баланс в БД")
    tx_hash: str = Field(..., description="Хэш onchain-транзакции")


class ProjectJoinByCodeRequest(BaseModel):
    """Запись на проект по коду приглашения."""

    code: str = Field(..., min_length=4, max_length=32, description="Код join_code проекта")


class ProjectJoinByCodeResponse(BaseModel):
    """Ответ после записи по коду."""

    project_id: int = Field(..., description="ID проекта")
    project_name: str = Field(..., description="Название проекта")
    token_balance: Decimal = Field(..., description="Баланс после mint")
    enrolled_at: datetime = Field(..., description="Время записи")
    tx_hash: str | None = Field(None, description="Хэш mint-транзакции")


class ProjectBalanceResponse(BaseModel):
    """Баланс пользователя в рамках одного проекта."""

    project_id: int = Field(..., description="ID проекта")
    available: Decimal = Field(..., description="Доступно onchain")
    frozen: Decimal = Field(..., description="Заморожено в ставках")
    pending_refund: Decimal = Field(..., description="Ожидаемый возврат")


class OrganizerStatsResponse(BaseModel):
    """Аналитика проекта для организатора."""

    project_id: int = Field(..., description="ID проекта")
    project_name: str = Field(..., description="Название")
    semester_label: str | None = Field(None, description="Метка семестра")
    members_count: int = Field(..., description="Число участников")
    members_trend_month: int = Field(..., description="Прирост участников за месяц")
    tokens_in_circulation: Decimal = Field(..., description="Токенов в обращении")
    tokens_trend_week: Decimal = Field(..., description="Динамика токенов за неделю")
    active_auctions_count: int = Field(..., description="Открытых аукционов")
    average_attendance_percent: int = Field(..., description="Средний % посещаемости")
    attendance_trend_month: int = Field(..., description="Тренд посещаемости")
    weekly_mints: list[dict] = Field(..., description="Записи на курс по дням")
    auction_activity_by_day: list[dict] = Field(..., description="Созданные аукционы по дням")


class AttendanceStatsResponse(BaseModel):
    """Статистика посещаемости по проекту."""

    project_id: int = Field(..., description="ID проекта")
    average_attendance_percent: int = Field(..., description="Средний % подтверждённых визитов")
    total_sessions: int = Field(..., description="Всего сессий (ставок)")
    my_visits: int | None = Field(None, description="Личные визиты студента")


class MyProjectResponse(BaseModel):
    """Проект из списка «Мои проекты»."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="ID проекта")
    name: str = Field(..., description="Название")
    organizer_id: UUID = Field(..., description="UUID организатора")
    is_active: bool = Field(..., description="Активен ли")
    token_balance: Decimal = Field(..., description="Onchain-баланс")
    enrolled_at: datetime = Field(..., description="Дата записи")
