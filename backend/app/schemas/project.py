"""
Pydantic-схемы для управления проектами.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    """Создание проекта организатором."""

    name: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    password: str = Field(..., description="Пароль организатора для расшифровки приватного ключа")
    refund_rate: Decimal = Field(default=Decimal("80.00"), examples=[Decimal("80.00")])
    penalty_schedule: list[int] = Field(default_factory=lambda: [10, 20, 30, 50])
    initial_supply: int = Field(default=1000, ge=1)

    @field_validator("penalty_schedule")
    @classmethod
    def _validate_penalty_schedule(cls, value: list[int]) -> list[int]:
        if len(value) != 4:
            raise ValueError("penalty_schedule must contain exactly 4 values")
        return value


class ProjectListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    organizer_id: UUID
    is_active: bool


class ProjectDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    organizer_id: UUID
    blockchain_id: int
    refund_rate: Decimal
    penalty_schedule: list[int]
    initial_supply: int
    is_active: bool
    join_code: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    blockchain_id: int
    join_code: str | None = None
    tx_hash: str


class EnrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    project_id: int
    enrolled_at: datetime
    token_balance: Decimal
    tx_hash: str


class ProjectMemberResponse(BaseModel):
    user_id: UUID
    student_id: str
    full_name: str
    wallet_address: str
    token_balance: Decimal
    enrolled_at: datetime


class MintTokensRequest(BaseModel):
    amount: int = Field(..., ge=1, le=1_000_000)


class MintTokensResponse(BaseModel):
    user_id: UUID
    project_id: int
    amount: int
    new_balance: Decimal
    tx_hash: str


class ProjectJoinByCodeRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32)


class ProjectJoinByCodeResponse(BaseModel):
    project_id: int
    project_name: str
    token_balance: Decimal
    enrolled_at: datetime
    tx_hash: str | None = None


class ProjectBalanceResponse(BaseModel):
    project_id: int
    available: Decimal
    frozen: Decimal
    pending_refund: Decimal


class OrganizerStatsResponse(BaseModel):
    project_id: int
    project_name: str
    semester_label: str | None
    members_count: int
    members_trend_month: int
    tokens_in_circulation: Decimal
    tokens_trend_week: Decimal
    active_auctions_count: int
    average_attendance_percent: int
    attendance_trend_month: int
    weekly_mints: list[dict]
    auction_activity_by_day: list[dict]


class AttendanceStatsResponse(BaseModel):
    project_id: int
    average_attendance_percent: int
    total_sessions: int
    my_visits: int | None = None


class MyProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    organizer_id: UUID
    is_active: bool
    token_balance: Decimal
    enrolled_at: datetime
