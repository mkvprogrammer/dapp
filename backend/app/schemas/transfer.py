from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class TransferCreate(BaseModel):
    recipient_student_id: str = Field(..., min_length=1, max_length=50)
    project_id: int
    amount: Decimal = Field(..., gt=0)
    comment: str | None = Field(None, max_length=500)
    password: str = Field(..., min_length=1)


class TransferResponse(BaseModel):
    id: UUID
    project_id: int
    sender_student_id: str
    recipient_student_id: str
    recipient_full_name: str
    amount: Decimal
    comment: str | None
    status: str
    tx_hash: str | None
    created_at: datetime


class TransferListItem(BaseModel):
    id: UUID
    direction: str
    counterparty_name: str
    counterparty_student_id: str
    amount: Decimal
    comment: str | None
    status: str
    created_at: datetime


class TransferListResponse(BaseModel):
    items: list[TransferListItem]
    total: int


class RecentRecipient(BaseModel):
    user_id: UUID
    student_id: str
    full_name: str


class RecentRecipientsResponse(BaseModel):
    items: list[RecentRecipient]


class WalletBalanceResponse(BaseModel):
    available: Decimal
    project_id: int | None = None
