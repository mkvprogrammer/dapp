"""
Агрегат данных для главной страницы.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
from app.models.notification import Notification
from app.models.project import Project, UserProject
from app.models.user import User
from app.services import user_service


async def get_dashboard(db: AsyncSession, user: User) -> dict:
    """Собирает данные главной страницы: балансы, проекты, аукционы, уведомления."""
    balances = await user_service.get_balances(db, user)
    now = datetime.now(UTC)

    enrollments = await db.execute(
        select(Project, UserProject)
        .join(UserProject, UserProject.project_id == Project.id)
        .where(UserProject.user_id == user.id, Project.is_active.is_(True))
    )
    projects_preview: list[dict] = []
    for project, _ep in enrollments.all():
        open_count = await db.scalar(
            select(func.count(Auction.id)).where(
                Auction.project_id == project.id,
                Auction.status == AuctionStatus.OPEN,
                Auction.end_time > now,
            )
        )
        bal = next(
            (p for p in balances["by_project"] if p["project_id"] == project.id),
            None,
        )
        projects_preview.append(
            {
                "project_id": project.id,
                "name": project.name,
                "token_balance": bal["available"] if bal else Decimal(0),
                "active_auctions_count": int(open_count or 0),
                "activity_percent": min(100, int(open_count or 0) * 10),
            }
        )

    enrolled_ids = select(UserProject.project_id).where(UserProject.user_id == user.id)
    open_result = await db.execute(
        select(Auction, Project, Bid)
        .join(Project, Project.id == Auction.project_id)
        .outerjoin(
            Bid,
            (Bid.auction_id == Auction.id)
            & (Bid.user_id == user.id)
            & (Bid.status == BidStatus.LOCKED),
        )
        .where(
            Auction.project_id.in_(enrolled_ids),
            Auction.status == AuctionStatus.OPEN,
            Auction.end_time > now,
        )
        .order_by(Auction.end_time.asc())
    )
    open_rows = list(open_result.all())
    active_auctions: list[dict] = []
    for auction, project, bid in open_rows[:5]:
        participants_count = await db.scalar(
            select(func.count(func.distinct(Bid.user_id))).where(
                Bid.auction_id == auction.id,
                Bid.status == BidStatus.LOCKED,
            )
        )
        my_rank = None
        if bid is not None:
            higher = await db.scalar(
                select(func.count(func.distinct(Bid.user_id))).where(
                    Bid.auction_id == auction.id,
                    Bid.status == BidStatus.LOCKED,
                    Bid.amount > bid.amount,
                )
            )
            my_rank = int(higher or 0) + 1
        active_auctions.append(
            {
                "auction_id": auction.id,
                "resource_name": auction.resource_name,
                "project_id": project.id,
                "project_name": project.name,
                "status": auction.status.value,
                "my_bid_amount": bid.amount if bid else None,
                "my_rank": my_rank,
                "participants_count": participants_count,
                "end_time": auction.end_time,
                "image_url": auction.image_url,
            }
        )

    unread = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.is_read.is_(False),
        )
    )

    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    wins = await db.scalar(
        select(func.count(Bid.id)).where(
            Bid.user_id == user.id,
            Bid.status == BidStatus.REFUNDED,
            Bid.created_at >= month_start,
        )
    )

    activity = await user_service.get_activity(db, user, limit=5, offset=0)

    return {
        "total_balance": balances["total"],
        "active_auctions_count": len(open_rows),
        "projects_count": len(projects_preview),
        "wins_this_month": int(wins or 0),
        "unread_notifications_count": int(unread or 0),
        "projects": projects_preview,
        "active_auctions": active_auctions,
        "recent_activity": activity["items"],
    }
