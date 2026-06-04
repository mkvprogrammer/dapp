from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardProjectPreview(BaseModel):
    project_id: int
    name: str
    token_balance: Decimal
    active_auctions_count: int
    activity_percent: int = Field(..., ge=0, le=100)


class DashboardAuctionPreview(BaseModel):
    auction_id: int
    resource_name: str
    project_id: int
    project_name: str
    status: str
    my_bid_amount: Decimal | None = None
    my_rank: int | None = None
    participants_count: int
    end_time: datetime
    image_url: str | None = None


class DashboardActivityPreview(BaseModel):
    id: UUID
    type: str
    title: str
    description: str
    amount_delta: Decimal | None = None
    created_at: datetime


class DashboardResponse(BaseModel):
    total_balance: Decimal
    active_auctions_count: int
    projects_count: int
    wins_this_month: int
    unread_notifications_count: int
    projects: list[DashboardProjectPreview]
    active_auctions: list[DashboardAuctionPreview]
    recent_activity: list[DashboardActivityPreview]
