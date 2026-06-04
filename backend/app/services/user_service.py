"""
Профиль, балансы и активность пользователя.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.blockchain import blockchain_service
from app.core.exceptions import UserNotFoundError
from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
from app.models.bid_event import BidEvent
from app.models.project import Project, UserProject
from app.models.transfer import Transfer
from app.models.user import User


async def get_profile(db: AsyncSession, user: User) -> dict:
    participations = await db.scalar(
        select(func.count(Bid.id)).where(Bid.user_id == user.id)
    )
    wins = await db.scalar(
        select(func.count(Bid.id)).where(
            Bid.user_id == user.id,
            Bid.status == BidStatus.CLAIMED,
        )
    )
    confirmed = await db.scalar(
        select(func.count(Bid.id)).where(
            Bid.user_id == user.id,
            Bid.status == BidStatus.REFUNDED,
        )
    )
    return {
        "user": user,
        "stats": {
            "won_auctions": int(wins or 0),
            "auction_participations": int(participations or 0),
            "tokens_earned": Decimal(0),
            "confirmed_attendance_hours": Decimal(confirmed or 0),
        },
    }


async def update_profile(
    db: AsyncSession,
    user: User,
    *,
    full_name: str | None,
    faculty: str | None,
) -> User:
    if full_name is not None:
        user.full_name = full_name
    if faculty is not None:
        user.faculty = faculty
    await db.commit()
    await db.refresh(user)
    return user


async def get_balances(db: AsyncSession, user: User) -> dict:
    enrollments = await db.execute(
        select(Project, UserProject)
        .join(UserProject, UserProject.project_id == Project.id)
        .where(UserProject.user_id == user.id)
    )
    by_project: list[dict] = []
    total = Decimal(0)
    frozen_total = Decimal(0)
    for project, _enrollment in enrollments.all():
        available = Decimal(
            await blockchain_service.get_token_balance(user.wallet_address, project.blockchain_id)
        )
        frozen_result = await db.execute(
            select(func.coalesce(func.sum(Bid.amount), 0)).where(
                Bid.user_id == user.id,
                Bid.status == BidStatus.LOCKED,
                Bid.auction_id.in_(select(Auction.id).where(Auction.project_id == project.id)),
            )
        )
        frozen = Decimal(frozen_result.scalar() or 0)
        by_project.append(
            {
                "project_id": project.id,
                "project_name": project.name,
                "available": available,
                "frozen": frozen,
                "pending_refund": Decimal(0),
            }
        )
        total += available + frozen
        frozen_total += frozen
    return {
        "total": total,
        "available": total - frozen_total,
        "frozen": frozen_total,
        "pending_refund": Decimal(0),
        "by_project": by_project,
    }


async def get_activity(db: AsyncSession, user: User, limit: int, offset: int) -> dict:
    items: list[dict] = []

    bids = await db.execute(
        select(BidEvent, Auction, Project)
        .join(Auction, Auction.id == BidEvent.auction_id)
        .join(Project, Project.id == Auction.project_id)
        .where(BidEvent.user_id == user.id)
        .order_by(BidEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    for event, auction, project in bids.all():
        items.append(
            {
                "id": event.id,
                "type": "auction_bid",
                "title": f"Ставка: {auction.resource_name}",
                "description": f"{event.action} · {project.name}",
                "project_id": project.id,
                "project_name": project.name,
                "amount_delta": -event.amount if event.action != "cancelled" else event.amount,
                "created_at": event.created_at,
            }
        )

    transfers = await db.execute(
        select(Transfer, Project)
        .join(Project, Project.id == Transfer.project_id)
        .where(
            (Transfer.sender_id == user.id) | (Transfer.recipient_id == user.id),
        )
        .order_by(Transfer.created_at.desc())
        .limit(limit)
    )
    for transfer, project in transfers.all():
        direction = "transfer_out" if transfer.sender_id == user.id else "transfer_in"
        items.append(
            {
                "id": transfer.id,
                "type": direction,
                "title": "Перевод токенов",
                "description": project.name,
                "project_id": project.id,
                "project_name": project.name,
                "amount_delta": -transfer.amount if direction == "transfer_out" else transfer.amount,
                "created_at": transfer.created_at,
            }
        )

    items.sort(key=lambda x: x["created_at"], reverse=True)
    page = items[offset : offset + limit]
    return {"items": page, "total": len(items)}


async def get_active_auctions(db: AsyncSession, user: User) -> list[dict]:
    now = datetime.now(UTC)
    result = await db.execute(
        select(Auction, Project, Bid)
        .join(Project, Project.id == Auction.project_id)
        .outerjoin(
            Bid,
            (Bid.auction_id == Auction.id) & (Bid.user_id == user.id) & (Bid.status == BidStatus.LOCKED),
        )
        .where(Auction.status == AuctionStatus.OPEN, Auction.end_time > now)
    )
    items: list[dict] = []
    for auction, project, bid in result.all():
        if bid is None:
            continue
        lb = await blockchain_service.get_leaderboard(auction.blockchain_auction_id, 50)
        rank = None
        for i, (wallet, _amount) in enumerate(lb):
            if wallet.lower() == user.wallet_address.lower():
                rank = i + 1
                break
        items.append(
            {
                "auction_id": auction.id,
                "project_id": project.id,
                "resource_name": auction.resource_name,
                "project_name": project.name,
                "my_bid_amount": bid.amount,
                "my_rank": rank or 0,
                "participants_count": len(lb),
                "end_time": auction.end_time,
                "time_left_seconds": max(0, int((auction.end_time - now).total_seconds())),
            }
        )
    return items
