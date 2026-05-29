"""
HTTP-ручки аукционов.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.auction import (
    AuctionCreate,
    AuctionCreatedResponse,
    AuctionDetailResponse,
    AuctionListResponse,
    BidCancelRequest,
    BidCreate,
    BidResponse,
    CancelBidResponse,
    LeaderboardEntry,
    LeaderboardResponse,
)
from app.services import auction_service
from database import get_db

router = APIRouter(prefix="/auctions", tags=["Auctions"])


@router.get("/", response_model=list[AuctionListResponse])
async def list_open_auctions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuctionListResponse]:
    """Список открытых аукционов."""
    auctions = await auction_service.get_open_auctions(db)
    return [AuctionListResponse.model_validate(a) for a in auctions]


@router.get("/{auction_id}", response_model=AuctionDetailResponse)
async def get_auction(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuctionDetailResponse:
    """Детали аукциона по ID."""
    auction = await auction_service.get_auction_by_id(db, auction_id)
    return AuctionDetailResponse.model_validate(auction)


@router.get("/{auction_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 10,
) -> LeaderboardResponse:
    """Лидерборд ставок аукциона."""
    await auction_service.get_auction_by_id(db, auction_id)
    entries_raw = await auction_service.get_leaderboard(db, auction_id, limit=limit)
    entries = [LeaderboardEntry(**row) for row in entries_raw]
    return LeaderboardResponse(auction_id=auction_id, entries=entries)


@router.post("/", response_model=AuctionCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_auction(
    payload: AuctionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER, UserRole.STUDENT])),
) -> AuctionCreatedResponse:
    """
    Создание аукциона.

    Организатор проекта или студент, записанный на курс.
    Onchain: msg.sender должен иметь USER_ROLE или ORGANIZER_ROLE (см. AuctionManager).
    """
    creator_private_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    auction, tx_hash = await auction_service.create_auction(
        db=db,
        schema=payload,
        creator=current_user,
        creator_private_key=creator_private_key,
    )
    return AuctionCreatedResponse(
        id=auction.id,
        resource_name=auction.resource_name,
        blockchain_auction_id=auction.blockchain_auction_id,
        tx_hash=tx_hash,
    )


@router.post("/{auction_id}/bid", response_model=BidResponse)
async def place_bid(
    auction_id: int,
    payload: BidCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.STUDENT])),
) -> BidResponse:
    """Ставка студента."""
    student_private_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    bid, tx_hash = await auction_service.place_bid(
        db=db,
        auction_id=auction_id,
        schema=payload,
        student=current_user,
        student_private_key=student_private_key,
    )
    return BidResponse(
        id=bid.id,
        auction_id=bid.auction_id,
        user_id=bid.user_id,
        amount=bid.amount,
        status=bid.status.value,
        tx_hash=tx_hash,
    )


@router.delete("/{auction_id}/bid", response_model=CancelBidResponse)
async def cancel_bid(
    auction_id: int,
    payload: BidCancelRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.STUDENT])),
) -> CancelBidResponse:
    """Отмена ставки студентом."""
    student_private_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    bid, tx_hash = await auction_service.cancel_bid(
        db=db,
        auction_id=auction_id,
        student=current_user,
        student_private_key=student_private_key,
    )
    return CancelBidResponse(
        auction_id=auction_id,
        status=bid.status.value,
        tx_hash=tx_hash,
    )
