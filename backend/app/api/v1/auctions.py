"""
HTTP-ручки аукционов.
"""

import asyncio
import json

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.auction import (
    AuctionCreate,
    AuctionCreatedResponse,
    AuctionDetailResponse,
    AuctionListResponse,
    AuctionListResponseExtended,
    BidHistoryEntry,
    BidHistoryResponse,
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


@router.get("/", response_model=list[AuctionListResponseExtended])
async def list_auctions(
    project_id: int | None = None,
    status: str = Query("all", pattern="^(open|closed|cancelled|all)$"),
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuctionListResponseExtended]:
    """Список аукционов с фильтрами; для текущего пользователя — его ставка и ранг."""
    rows = await auction_service.list_auctions(
        db, user=current_user, project_id=project_id, status=status, search=search
    )
    return [AuctionListResponseExtended(**row) for row in rows]


@router.get("/{auction_id}/bid-history", response_model=BidHistoryResponse)
async def bid_history(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BidHistoryResponse:
    """История событий ставок по аукциону (размещение, повышение, отмена)."""
    entries = await auction_service.get_bid_history(db, auction_id)
    return BidHistoryResponse(
        auction_id=auction_id,
        entries=[BidHistoryEntry(**e) for e in entries],
    )


@router.get("/{auction_id}/stream")
async def auction_stream(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSE: обновления лидерборда каждые 5 с."""

    async def event_generator():
        while True:
            entries_raw = await auction_service.get_leaderboard(db, auction_id, limit=20)
            payload = {
                "type": "leaderboard_update",
                "auction_id": auction_id,
                "entries": entries_raw,
            }
            yield f"data: {json.dumps(payload, default=str)}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
