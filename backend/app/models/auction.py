from __future__ import annotations

import enum
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, DateTime, ForeignKey, Integer, BigInteger, Numeric, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# 1. Создаем Enum для статусов аукциона (защита от опечаток в строках)
class AuctionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

# 2. Создаем Enum для статусов ставок студента
class BidStatus(str, enum.Enum):
    LOCKED = "locked"      # Ставка заблокирована на аукционе
    REFUNDED = "refunded"  # Токены вернулись студенту (после отмены или проигрыша)
    BURNED = "burned"      # Токены сгорели в качестве штрафа за позднюю отмену
    CLAIMED = "claimed"    # Аукцион завершен, и ставка зафиксирована


class Auction(Base):
    __tablename__ = "auctions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    resource_name: Mapped[str] = mapped_column(String(150))
    
    # В SQLAlchemy 2.0 поля Mapped[datetime] автоматически становятся NOT NULL в БД
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lesson_start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    resource_limit: Mapped[int] = mapped_column(Integer)  # Количество мест для победителей (например, 2)
    blockchain_auction_id: Mapped[int] = mapped_column(BigInteger, unique=True) # ID аукциона в Solidity
    
    # Применяем созданный Enum. native_enum=False сохранит его в базе как обычную строку (VARCHAR)
    status: Mapped[AuctionStatus] = mapped_column(
        Enum(AuctionStatus, native_enum=False), 
        default=AuctionStatus.OPEN
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ORM Связи (Relationships)
    bids: Mapped[list[Bid]] = relationship("Bid", back_populates="auction", cascade="all, delete-orphan")


class Bid(Base):
    __tablename__ = "bids"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    auction_id: Mapped[int] = mapped_column(ForeignKey("auctions.id"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    
    # Суммы ставок в блокчейне (uint256) огромные. Numeric(78, 0) переводится в Decimal в Python
    amount: Mapped[Decimal] = mapped_column(Numeric(78, 0))
    
    # Применяем Enum для статуса ставки
    status: Mapped[BidStatus] = mapped_column(
        Enum(BidStatus, native_enum=False), 
        default=BidStatus.LOCKED
    )
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ORM Связи (Relationships)
    auction: Mapped[Auction] = relationship("Auction", back_populates="bids")
