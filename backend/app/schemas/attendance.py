"""
Схемы посещаемости: подтверждение преподавателем (без кодов).
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizerActionRequest(BaseModel):
    """Пароль организатора для подписи onchain-транзакции."""

    password: str = Field(..., min_length=1)


class AttendanceStudentRequest(OrganizerActionRequest):
    """Действие по конкретному студенту (ITMO ID)."""

    student_id: str = Field(..., min_length=1, max_length=50)


class AttendanceTxResponse(BaseModel):
    auction_id: int
    student_id: str | None = None
    tx_hash: str
    message: str


class AttendanceEntry(BaseModel):
    user_id: UUID
    student_id: str
    full_name: str
    wallet_address: str
    bid_amount: Decimal
    bid_status: str
    attendance_label: str  # pending | present | absent | no_bid


class AttendanceListResponse(BaseModel):
    auction_id: int
    resource_name: str
    lesson_start_time: str
    entries: list[AttendanceEntry]
