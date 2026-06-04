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

    new_role: UserRole


class AdminUserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(validation_alias="id")
    student_id: str
    full_name: str
    wallet_address: str
    role: str
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def _role_as_str(cls, value: str | Enum) -> str:
        if isinstance(value, Enum):
            return value.value
        return value


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int


class AuditLogEntry(BaseModel):
    id: UUID
    created_at: datetime
    actor_name: str
    actor_student_id: str | None
    action: str
    object_ref: str
    ip_address: str | None


class AuditLogResponse(BaseModel):
    items: list[AuditLogEntry]
    total: int


class EmergencyStopRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=500)


class EmergencyStopResponse(BaseModel):
    stopped_auctions_count: int
    message: str


class ServiceHealth(BaseModel):
    name: str
    status: str
    detail: str
    latency_ms: int | None = None


class AdminHealthResponse(BaseModel):
    services: list[ServiceHealth]
    active_auctions: int
    bids_per_hour: int
    blockchain_block_number: int | None

