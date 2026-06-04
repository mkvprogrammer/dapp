"""
Посещаемость: преподаватель подтверждает присутствие / отмечает прогул / закрывает день.
Коды подтверждения не используются.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.blockchain import blockchain_service
from app.core.notify import push_notification
from app.models.notification import NotificationType
from app.core.exceptions import (
    AuctionNotFoundError,
    AuctionTimeError,
    BlockchainCommunicationError,
    DatabasePersistenceError,
    ProjectAccessDeniedError,
    StudentNotInAuctionError,
    UserNotFoundError,
)
from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
from app.models.project import Project
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def _get_auction_with_project(db: AsyncSession, auction_id: int) -> tuple[Auction, Project]:
    result = await db.execute(
        select(Auction, Project)
        .join(Project, Project.id == Auction.project_id)
        .where(Auction.id == auction_id)
    )
    row = result.one_or_none()
    if row is None:
        raise AuctionNotFoundError()
    return row[0], row[1]


def _assert_organizer_may_manage(organizer: User, project: Project) -> None:
    if organizer.role != UserRole.ORGANIZER or project.organizer_id != organizer.id:
        raise ProjectAccessDeniedError()


async def _get_student_bid(
    db: AsyncSession,
    auction_id: int,
    student_id: str,
) -> tuple[User, Bid]:
    user_result = await db.execute(select(User).where(User.student_id == student_id))
    student = user_result.scalar_one_or_none()
    if student is None:
        raise UserNotFoundError()

    bid_result = await db.execute(
        select(Bid).where(
            Bid.auction_id == auction_id,
            Bid.user_id == student.id,
            Bid.status == BidStatus.LOCKED,
        )
    )
    bid = bid_result.scalar_one_or_none()
    if bid is None or bid.amount <= 0:
        raise StudentNotInAuctionError()
    return student, bid


def _attendance_label(bid: Bid | None) -> str:
    if bid is None or bid.amount <= 0:
        return "no_bid"
    if bid.status == BidStatus.REFUNDED:
        return "present"
    if bid.status == BidStatus.ABSENT:
        return "absent"
    if bid.status == BidStatus.BURNED:
        return "penalized"
    if bid.status == BidStatus.LOCKED:
        return "pending"
    return bid.status.value


async def list_attendance(
    db: AsyncSession,
    auction_id: int,
    viewer: User,
) -> tuple[Auction, list[dict]]:
    auction, project = await _get_auction_with_project(db, auction_id)
    _assert_organizer_may_manage(viewer, project)

    result = await db.execute(
        select(Bid)
        .where(Bid.auction_id == auction_id)
    )
    bids = list(result.scalars().all())

    user_ids = {b.user_id for b in bids}
    users_map: dict = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u for u in users_result.scalars().all()}

    entries: list[dict] = []
    for bid in bids:
        user = users_map.get(bid.user_id)
        if user is None:
            continue
        entries.append(
            {
                "user_id": user.id,
                "student_id": user.student_id,
                "full_name": user.full_name,
                "wallet_address": user.wallet_address,
                "bid_amount": bid.amount,
                "bid_status": bid.status.value,
                "attendance_label": _attendance_label(bid),
            }
        )

    entries.sort(key=lambda e: (-int(e["bid_amount"]), e["student_id"]))
    return auction, entries


async def confirm_presence(
    db: AsyncSession,
    auction_id: int,
    student_id: str,
    organizer: User,
    organizer_private_key: str,
) -> tuple[str, str]:
    """Подтверждение присутствия: processAttendanceRefund on-chain."""
    auction, project = await _get_auction_with_project(db, auction_id)
    _assert_organizer_may_manage(organizer, project)

    student, bid = await _get_student_bid(db, auction_id, student_id)

    try:
        tx_hash = await blockchain_service.process_attendance_refund_onchain(
            blockchain_auction_id=auction.blockchain_auction_id,
            student_wallet=student.wallet_address,
            organizer_private_key=organizer_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("processAttendanceRefund failed")
        raise BlockchainCommunicationError() from exc

    bid.status = BidStatus.REFUNDED
    bid.amount = Decimal(0)

    await push_notification(
        db,
        user_id=student.id,
        ntype=NotificationType.ATTENDANCE_CONFIRMED.value,
        title="Посещение подтверждено",
        body=f"Преподаватель подтвердил ваше присутствие на «{auction.resource_name}»",
        meta={"auction_id": auction_id, "project_id": project.id},
    )

    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise DatabasePersistenceError() from exc

    return tx_hash, student.student_id


async def mark_student_absent(
    db: AsyncSession,
    auction_id: int,
    student_id: str,
    organizer: User,
    organizer_private_key: str,
) -> tuple[str, str]:
    auction, project = await _get_auction_with_project(db, auction_id)
    _assert_organizer_may_manage(organizer, project)

    student, bid = await _get_student_bid(db, auction_id, student_id)

    try:
        tx_hash = await blockchain_service.mark_as_absent_onchain(
            blockchain_auction_id=auction.blockchain_auction_id,
            student_wallet=student.wallet_address,
            organizer_private_key=organizer_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("markAsAbsent failed")
        raise BlockchainCommunicationError() from exc

    bid.status = BidStatus.ABSENT

    await push_notification(
        db,
        user_id=student.id,
        ntype=NotificationType.SYSTEM.value,
        title="Отмечен прогул",
        body=f"По аукциону «{auction.resource_name}» зафиксирован прогул",
        meta={"auction_id": auction_id, "project_id": project.id},
    )

    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise DatabasePersistenceError() from exc

    return tx_hash, student.student_id


async def close_lesson_day(
    db: AsyncSession,
    auction_id: int,
    organizer: User,
    organizer_private_key: str,
) -> str:
    auction, project = await _get_auction_with_project(db, auction_id)
    _assert_organizer_may_manage(organizer, project)

    now = datetime.now(UTC)
    if auction.lesson_start_time > now:
        raise AuctionTimeError()

    try:
        tx_hash = await blockchain_service.close_day_and_refund_remaining_onchain(
            blockchain_auction_id=auction.blockchain_auction_id,
            organizer_private_key=organizer_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("closeDayAndRefundRemaining failed")
        raise BlockchainCommunicationError() from exc

    bids_result = await db.execute(
        select(Bid).where(
            Bid.auction_id == auction_id,
            Bid.status.in_([BidStatus.LOCKED, BidStatus.ABSENT]),
        )
    )
    for bid in bids_result.scalars().all():
        if bid.status == BidStatus.ABSENT:
            bid.status = BidStatus.BURNED
        else:
            bid.status = BidStatus.REFUNDED
        bid.amount = Decimal(0)

    auction.status = AuctionStatus.CLOSED

    try:
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise DatabasePersistenceError() from exc

    return tx_hash
