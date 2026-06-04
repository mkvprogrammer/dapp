from __future__ import annotations

import enum
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class BidEventAction(str, enum.Enum):
    PLACED = "placed"
    RAISED = "raised"
    CANCELLED = "cancelled"


class BidEvent(Base):
    __tablename__ = "bid_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auctions.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(78, 0))
    action: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
