from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserStatsResponse(BaseModel):
    won_auctions: int
    auction_participations: int
    tokens_earned: Decimal
    confirmed_attendance_hours: Decimal


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(validation_alias="id")
    student_id: str
    full_name: str
    faculty: str | None = None
    wallet_address: str
    role: str
    stats: UserStatsResponse
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def _role_str(cls, v):
        return v.value if hasattr(v, "value") else v


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=150)
    faculty: str | None = Field(None, max_length=200)


class ProjectBalanceItem(BaseModel):
    project_id: int
    project_name: str
    available: Decimal
    frozen: Decimal
    pending_refund: Decimal


class UserBalancesResponse(BaseModel):
    total: Decimal
    available: Decimal
    frozen: Decimal
    pending_refund: Decimal
    by_project: list[ProjectBalanceItem]


class ActivityItem(BaseModel):
    id: UUID
    type: str
    title: str
    description: str
    project_id: int | None = None
    project_name: str | None = None
    amount_delta: Decimal | None = None
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityItem]
    total: int


class MyActiveAuctionItem(BaseModel):
    auction_id: int
    project_id: int
    resource_name: str
    project_name: str
    my_bid_amount: Decimal
    my_rank: int
    participants_count: int
    end_time: datetime
    time_left_seconds: int


class MyActiveAuctionsResponse(BaseModel):
    items: list[MyActiveAuctionItem]
