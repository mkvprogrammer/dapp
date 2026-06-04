from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class NotificationMeta(BaseModel):
    project_id: int | None = None
    project_name: str | None = None
    auction_id: int | None = None
    bid_amount: Decimal | None = None
    rank: int | None = None
    balance_after: Decimal | None = None
    action_url: str | None = None


class NotificationItem(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    meta: dict
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int
    unread_count: int


class NotificationReadResponse(BaseModel):
    id: UUID
    is_read: bool


class NotificationReadAllResponse(BaseModel):
    updated_count: int
