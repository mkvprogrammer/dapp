"""
Схемы посещаемости: подтверждение преподавателем (без кодов).
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrganizerActionRequest(BaseModel):
    """Пароль организатора для подписи onchain-транзакции."""

    password: str = Field(..., min_length=1, description="Пароль для расшифровки ключа")


class AttendanceStudentRequest(OrganizerActionRequest):
    """Действие по конкретному студенту (ITMO ID)."""

    student_id: str = Field(..., min_length=1, max_length=50, description="ID студента")


class AttendanceTxResponse(BaseModel):
    """Ответ после onchain-операции посещаемости."""

    auction_id: int = Field(..., description="ID аукциона")
    student_id: str | None = Field(None, description="ID студента (если применимо)")
    tx_hash: str = Field(..., description="Хэш транзакции")
    message: str = Field(..., description="Сообщение для UI")


class AttendanceEntry(BaseModel):
    """Участник аукциона со статусом посещаемости."""

    user_id: UUID = Field(..., description="UUID студента")
    student_id: str = Field(..., description="ID студента")
    full_name: str = Field(..., description="ФИО")
    wallet_address: str = Field(..., description="Адрес кошелька")
    bid_amount: Decimal = Field(..., description="Сумма ставки")
    bid_status: str = Field(..., description="Статус ставки в БД")
    attendance_label: str = Field(..., description="pending | present | absent | no_bid | penalized")


class AttendanceListResponse(BaseModel):
    """Список участников аукциона для учёта посещаемости."""

    auction_id: int = Field(..., description="ID аукциона")
    resource_name: str = Field(..., description="Название ресурса")
    lesson_start_time: str = Field(..., description="Время начала занятия (ISO)")
    entries: list[AttendanceEntry] = Field(..., description="Участники со ставками")
