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
    created_at: datetime
    updated_at: datetime


class ProjectCreatedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    blockchain_id: int
    tx_hash: str


class EnrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    project_id: int
    enrolled_at: datetime
    token_balance: Decimal
    tx_hash: str
