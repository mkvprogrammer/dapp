"""Периодическое обслуживание (Celery)."""

from datetime import UTC, datetime

from app.worker import celery_app


@celery_app.task(name="app.tasks.maintenance.mark_expired_auctions_closed")
def mark_expired_auctions_closed() -> int:
    """Помечает просроченные open-аукционы как closed и уведомляет участников."""
    import asyncio

    from sqlalchemy import select

    from app.core.notify import push_notification
    from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
    from app.models.notification import NotificationType
    from app.models.user import User
    from database import async_session_factory

    async def _run() -> int:
        now = datetime.now(UTC)
        async with async_session_factory() as db:
            result = await db.execute(
                select(Auction).where(
                    Auction.status == AuctionStatus.OPEN,
                    Auction.end_time <= now,
                )
            )
            auctions = list(result.scalars().all())
            for auction in auctions:
                auction.status = AuctionStatus.CLOSED
                bids_result = await db.execute(
                    select(Bid, User)
                    .join(User, User.id == Bid.user_id)
                    .where(
                        Bid.auction_id == auction.id,
                        Bid.status == BidStatus.LOCKED,
                        Bid.amount > 0,
                    )
                )
                for _bid, participant in bids_result.all():
                    await push_notification(
                        db,
                        user_id=participant.id,
                        ntype=NotificationType.AUCTION_ENDING.value,
                        title="Аукцион завершён",
                        body=f"Торги по «{auction.resource_name}» закончились. Проверьте итоговый рейтинг.",
                        meta={"auction_id": auction.id, "project_id": auction.project_id},
                    )
            await db.commit()
            return len(auctions)

    return asyncio.run(_run())
