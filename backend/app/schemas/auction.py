"""
Pydantic-схемы для аукционов и ставок.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuctionCreate(BaseModel):
    project_id: int
    resource_name: str = Field(..., min_length=3, max_length=150)
    duration_seconds: int = Field(..., gt=0)
    lesson_start_time: datetime
    resource_limit: int = Field(..., gt=0)
    password: str = Field(..., description="Пароль организатора для подписи транзакции")
    resource_type: str = Field(default="consultation", max_length=32)
    location: str | None = Field(None, max_length=200)
    description: str | None = None
    min_bid: Decimal = Field(default=Decimal("1"), gt=0)
    bid_step: Decimal = Field(default=Decimal("1"), gt=0)
    image_url: str | None = Field(None, max_length=500)


def _enum_to_str(value: str | Enum) -> str:
    if isinstance(value, Enum):
        return value.value
    return value


class AuctionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    resource_name: str
    resource_limit: int
    status: str

    @field_validator("status", mode="before")
    @classmethod
    def _status_as_str(cls, value: str | Enum) -> str:
        return _enum_to_str(value)


class AuctionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    resource_name: str
    start_time: datetime
    end_time: datetime
    lesson_start_time: datetime
    resource_limit: int
    blockchain_auction_id: int
    status: str
    resource_type: str | None = None
    location: str | None = None
    description: str | None = None
    min_bid: Decimal | None = None
    bid_step: Decimal | None = None
    image_url: str | None = None
    created_at: datetime

    @field_validator("status", mode="before")
    @classmethod
    def _status_as_str(cls, value: str | Enum) -> str:
        return _enum_to_str(value)


class AuctionCreatedResponse(BaseModel):
    id: int
    resource_name: str
    blockchain_auction_id: int
    tx_hash: str


class BidCreate(BaseModel):
    amount: Decimal = Field(..., gt=0)
    password: str = Field(..., description="Пароль студента для approve/placeBid")


class BidCancelRequest(BaseModel):
    password: str


class BidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    auction_id: int
    user_id: UUID
    amount: Decimal
    status: str
    tx_hash: str


class LeaderboardEntry(BaseModel):
    wallet_address: str
    student_id: str
    full_name: str
    amount: Decimal
    is_guaranteed: bool


class LeaderboardResponse(BaseModel):
    auction_id: int
    entries: list[LeaderboardEntry]


class CancelBidResponse(BaseModel):
    auction_id: int
    status: str
    tx_hash: str


class AuctionListResponseExtended(BaseModel):
    id: int
    project_id: int
    project_name: str
    resource_name: str
    resource_limit: int
    status: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    current_top_bid: Decimal | None = None
    participants_count: int = 0
    my_bid_amount: Decimal | None = None
    my_rank: int | None = None
    image_url: str | None = None


class BidHistoryEntry(BaseModel):
    id: UUID
    student_id: str
    full_name: str
    amount: Decimal
    action: str
    created_at: datetime


class BidHistoryResponse(BaseModel):
    auction_id: int
    entries: list[BidHistoryEntry]
