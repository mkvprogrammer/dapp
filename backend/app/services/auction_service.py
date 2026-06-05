"""
Бизнес-логика аукционов (без HTTP-слоя).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from web3 import Web3

from app.core.audit_helper import write_audit
from app.core.blockchain import blockchain_service
from app.core.notify import push_notification
from app.models.notification import NotificationType
from app.core.exceptions import (
    AuctionClosedError,
    AuctionNotFoundError,
    BidAmountTooLowError,
    AuctionTimeError,
    BlockchainCommunicationError,
    BidNotFoundError,
    DatabasePersistenceError,
    InsufficientTokensError,
    NotEnrolledInProjectError,
    ProjectAccessDeniedError,
    ProjectInactiveError,
    ProjectNotFoundError,
)
from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
from app.models.bid_event import BidEvent, BidEventAction
from app.models.project import Project, UserProject
from app.models.user import User, UserRole
from app.schemas.auction import AuctionCreate, BidCreate

logger = logging.getLogger(__name__)


def _to_utc(dt: datetime) -> datetime:
    """Приводит datetime к UTC (naive считается UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


async def _assert_user_may_create_auction(
    db: AsyncSession,
    creator: User,
    project: Project,
) -> None:
    """
    Правила бэкенда (дополняют контракт AuctionManager.createAuction).

    Onchain достаточно USER_ROLE или ORGANIZER_ROLE у msg.sender.
    Здесь дополнительно:
    - организатор курса — только владелец проекта (projects.organizer_id);
    - студент — только если записан на курс (user_projects), с USER_ROLE после регистрации/enroll.
    """
    if not project.is_active:
        raise ProjectInactiveError()

    if creator.role == UserRole.ORGANIZER:
        if project.organizer_id != creator.id:
            raise ProjectAccessDeniedError()
        return

    if creator.role == UserRole.STUDENT:
        enrolled = await db.execute(
            select(UserProject).where(
                UserProject.user_id == creator.id,
                UserProject.project_id == project.id,
            )
        )
        if enrolled.scalar_one_or_none() is None:
            raise NotEnrolledInProjectError(
                "Сначала запишитесь на проект, чтобы создать аукцион"
            )
        return

    raise ProjectAccessDeniedError()


async def create_auction(
    db: AsyncSession,
    schema: AuctionCreate,
    creator: User,
    creator_private_key: str,
) -> tuple[Auction, str]:
    """
    Создаёт аукцион onchain и сохраняет запись в PostgreSQL.

    Транзакцию подписывает создатель (creator_private_key), не админ бэкенда.
    Onchain (AuctionManager): createAuction требует USER_ROLE или ORGANIZER_ROLE у msg.sender.
    """
    now = datetime.now(UTC)
    lesson_start = _to_utc(schema.lesson_start_time)
    trading_end = now + timedelta(seconds=schema.duration_seconds)

    if lesson_start <= now or lesson_start <= trading_end:
        raise AuctionTimeError()

    project_result = await db.execute(select(Project).where(Project.id == schema.project_id))
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError()

    await _assert_user_may_create_auction(db, creator, project)

    lesson_start_ts = int(lesson_start.timestamp())

    try:
        blockchain_auction_id, tx_hash = await blockchain_service.create_auction_onchain(
            project_blockchain_id=project.blockchain_id,
            resource_name=schema.resource_name,
            duration_seconds=schema.duration_seconds,
            lesson_start_ts=lesson_start_ts,
            resource_limit=schema.resource_limit,
            creator_private_key=creator_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create auction on-chain")
        raise BlockchainCommunicationError() from exc

    start_time = now
    end_time = start_time + timedelta(seconds=schema.duration_seconds)

    auction = Auction(
        id=blockchain_auction_id,
        project_id=schema.project_id,
        resource_name=schema.resource_name,
        start_time=start_time,
        end_time=end_time,
        lesson_start_time=lesson_start,
        resource_limit=schema.resource_limit,
        blockchain_auction_id=blockchain_auction_id,
        status=AuctionStatus.OPEN,
        resource_type=schema.resource_type,
        location=schema.location,
        description=schema.description,
        min_bid=schema.min_bid,
        bid_step=schema.bid_step,
        image_url=schema.image_url,
    )

    db.add(auction)
    await write_audit(
        db,
        event_type="auction",
        action="create_auction",
        object_ref=f"auction:{blockchain_auction_id} project:{schema.project_id}",
        actor_id=creator.id,
    )

    try:
        await db.commit()
        await db.refresh(auction)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist auction in database")
        raise DatabasePersistenceError() from exc

    return auction, tx_hash


async def _get_auction_or_raise(db: AsyncSession, auction_id: int) -> Auction:
    """Возвращает аукцион по ID или выбрасывает AuctionNotFoundError."""
    result = await db.execute(select(Auction).where(Auction.id == auction_id))
    auction = result.scalar_one_or_none()
    if auction is None:
        raise AuctionNotFoundError()
    return auction


def _ensure_auction_open(auction: Auction) -> None:
    """Проверяет, что аукцион открыт и торги ещё не завершены."""
    now = datetime.now(UTC)
    if auction.status != AuctionStatus.OPEN or auction.end_time <= now:
        raise AuctionClosedError()


async def place_bid(
    db: AsyncSession,
    auction_id: int,
    schema: BidCreate,
    student: User,
    student_private_key: str,
) -> tuple[Bid, str]:
    """Размещает или увеличивает ставку студента."""
    auction = await _get_auction_or_raise(db, auction_id)
    _ensure_auction_open(auction)

    project_result = await db.execute(select(Project).where(Project.id == auction.project_id))
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError()

    bid_amount = int(schema.amount)
    if auction.min_bid is not None and Decimal(bid_amount) < auction.min_bid:
        raise BidAmountTooLowError()
    balance = await blockchain_service.get_token_balance(
        student.wallet_address,
        project.blockchain_id,
    )
    if balance < bid_amount:
        raise InsufficientTokensError()

    try:
        tx_hash = await blockchain_service.place_bid_onchain(
            blockchain_auction_id=auction.blockchain_auction_id,
            amount=bid_amount,
            student_private_key=student_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to place bid on-chain")
        raise BlockchainCommunicationError() from exc

    bid_result = await db.execute(
        select(Bid).where(Bid.auction_id == auction_id, Bid.user_id == student.id)
    )
    bid = bid_result.scalar_one_or_none()

    action = BidEventAction.PLACED.value
    if bid is None:
        bid = Bid(
            auction_id=auction_id,
            user_id=student.id,
            amount=Decimal(bid_amount),
            status=BidStatus.LOCKED,
        )
        db.add(bid)
    else:
        bid.amount += Decimal(bid_amount)
        bid.status = BidStatus.LOCKED
        action = BidEventAction.RAISED.value

    db.add(
        BidEvent(
            auction_id=auction_id,
            user_id=student.id,
            amount=Decimal(bid_amount),
            action=action,
        )
    )

    lb = await blockchain_service.get_leaderboard(
        auction.blockchain_auction_id, limit=auction.resource_limit + 10
    )
    top_wallets = {w.lower() for w, _ in lb[: auction.resource_limit]}

    other_bids = await db.execute(
        select(Bid, User)
        .join(User, User.id == Bid.user_id)
        .where(Bid.auction_id == auction_id, Bid.status == BidStatus.LOCKED, Bid.user_id != student.id)
    )
    for _bid, other_user in other_bids.all():
        if other_user.wallet_address.lower() not in top_wallets:
            await push_notification(
                db,
                user_id=other_user.id,
                ntype=NotificationType.BID_OUTBID.value,
                title="Вас перебили",
                body=f"Ставка на «{auction.resource_name}» больше не в гарантированном топе",
                meta={"auction_id": auction_id, "project_id": auction.project_id},
            )

    try:
        await db.commit()
        await db.refresh(bid)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist bid in database")
        raise DatabasePersistenceError() from exc

    return bid, tx_hash


async def cancel_bid(
    db: AsyncSession,
    auction_id: int,
    student: User,
    student_private_key: str,
) -> tuple[Bid, str]:
    """Отменяет активную ставку студента."""
    auction = await _get_auction_or_raise(db, auction_id)

    bid_result = await db.execute(
        select(Bid).where(
            Bid.auction_id == auction_id,
            Bid.user_id == student.id,
            Bid.status == BidStatus.LOCKED,
        )
    )
    bid = bid_result.scalar_one_or_none()
    if bid is None:
        raise BidNotFoundError()

    try:
        tx_hash = await blockchain_service.cancel_bid_onchain(
            blockchain_auction_id=auction.blockchain_auction_id,
            student_private_key=student_private_key,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to cancel bid on-chain")
        raise BlockchainCommunicationError() from exc

    now = datetime.now(UTC)
    if now < auction.end_time:
        bid.status = BidStatus.REFUNDED
    else:
        # Торги завершены — возможен штраф (упрощённо помечаем как burned)
        bid.status = BidStatus.BURNED

    bid.amount = Decimal(0)
    db.add(
        BidEvent(
            auction_id=auction_id,
            user_id=student.id,
            amount=Decimal(0),
            action=BidEventAction.CANCELLED.value,
        )
    )

    try:
        await db.commit()
        await db.refresh(bid)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist bid cancellation in database")
        raise DatabasePersistenceError() from exc

    return bid, tx_hash


async def list_auctions(
    db: AsyncSession,
    *,
    user: User | None,
    project_id: int | None,
    status: str,
    search: str | None,
) -> list[dict]:
    """Список аукционов с агрегатами: топ-ставка, участники, ставка и ранг текущего user."""
    now = datetime.now(UTC)
    q = select(Auction, Project).join(Project, Project.id == Auction.project_id)
    if project_id is not None:
        q = q.where(Auction.project_id == project_id)
    if status == "open":
        q = q.where(Auction.status == AuctionStatus.OPEN, Auction.end_time > now)
    elif status == "closed":
        q = q.where(Auction.status == AuctionStatus.CLOSED)
    elif status == "cancelled":
        q = q.where(Auction.status == AuctionStatus.CANCELLED)
    if search:
        q = q.where(Auction.resource_name.ilike(f"%{search}%"))
    q = q.order_by(Auction.id.desc())
    result = await db.execute(q)
    pairs = result.all()
    if not pairs:
        return []

    auction_ids = [auction.id for auction, _ in pairs]

    top_rows = await db.execute(
        select(Bid.auction_id, func.max(Bid.amount))
        .where(Bid.auction_id.in_(auction_ids), Bid.status == BidStatus.LOCKED)
        .group_by(Bid.auction_id)
    )
    top_by_auction = {aid: Decimal(amount) for aid, amount in top_rows.all()}

    count_rows = await db.execute(
        select(Bid.auction_id, func.count(func.distinct(Bid.user_id)))
        .where(Bid.auction_id.in_(auction_ids), Bid.status == BidStatus.LOCKED)
        .group_by(Bid.auction_id)
    )
    participants_by_auction = {aid: int(cnt) for aid, cnt in count_rows.all()}

    my_bid_by_auction: dict[int, Decimal] = {}
    if user:
        my_rows = await db.execute(
            select(Bid.auction_id, Bid.amount).where(
                Bid.auction_id.in_(auction_ids),
                Bid.user_id == user.id,
                Bid.status == BidStatus.LOCKED,
            )
        )
        my_bid_by_auction = {aid: amount for aid, amount in my_rows.all()}

    rows: list[dict] = []
    for auction, project in pairs:
        my_bid = my_bid_by_auction.get(auction.id)
        my_rank = None
        if my_bid is not None:
            higher = await db.scalar(
                select(func.count(func.distinct(Bid.user_id))).where(
                    Bid.auction_id == auction.id,
                    Bid.status == BidStatus.LOCKED,
                    Bid.amount > my_bid,
                )
            )
            my_rank = int(higher or 0) + 1

        rows.append(
            {
                "id": auction.id,
                "project_id": auction.project_id,
                "project_name": project.name,
                "resource_name": auction.resource_name,
                "resource_limit": auction.resource_limit,
                "status": auction.status.value,
                "start_time": auction.start_time,
                "end_time": auction.end_time,
                "current_top_bid": top_by_auction.get(auction.id),
                "participants_count": participants_by_auction.get(auction.id, 0),
                "my_bid_amount": my_bid,
                "my_rank": my_rank,
                "image_url": auction.image_url,
            }
        )
    return rows


async def get_bid_history(db: AsyncSession, auction_id: int) -> list[dict]:
    """Хронология событий ставок (BidEvent) с данными студентов."""
    await _get_auction_or_raise(db, auction_id)
    result = await db.execute(
        select(BidEvent, User)
        .join(User, User.id == BidEvent.user_id)
        .where(BidEvent.auction_id == auction_id)
        .order_by(BidEvent.created_at.desc())
    )
    return [
        {
            "id": event.id,
            "student_id": user.student_id,
            "full_name": user.full_name,
            "amount": event.amount,
            "action": event.action,
            "created_at": event.created_at,
        }
        for event, user in result.all()
    ]


async def get_open_auctions(db: AsyncSession) -> list[Auction]:
    """Список открытых аукционов (status=OPEN и end_time в будущем)."""
    now = datetime.now(UTC)
    result = await db.execute(
        select(Auction)
        .where(Auction.status == AuctionStatus.OPEN, Auction.end_time > now)
        .order_by(Auction.id)
    )
    return list(result.scalars().all())


async def get_auction_by_id(db: AsyncSession, auction_id: int) -> Auction:
    """Публичная обёртка: аукцион по ID или AuctionNotFoundError."""
    return await _get_auction_or_raise(db, auction_id)


async def get_leaderboard(
    db: AsyncSession,
    auction_id: int,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Лидерборд: данные из блокчейна + профили студентов из PostgreSQL.
    """
    auction = await _get_auction_or_raise(db, auction_id)

    raw_entries = await blockchain_service.get_leaderboard(
        blockchain_auction_id=auction.blockchain_auction_id,
        limit=limit,
    )

    # Сортируем по сумме ставки (убывание) для корректного топа
    raw_entries.sort(key=lambda item: item[1], reverse=True)

    leaderboard: list[dict[str, Any]] = []
    for index, (wallet, amount) in enumerate(raw_entries):
        wallet_checksum = Web3.to_checksum_address(wallet)
        user_result = await db.execute(
            select(User).where(User.wallet_address == wallet_checksum)
        )
        user = user_result.scalar_one_or_none()

        # Топ-N по сумме ставки получают гарантированное место
        is_guaranteed = index < auction.resource_limit

        leaderboard.append(
            {
                "wallet_address": wallet,
                "student_id": user.student_id if user else "",
                "full_name": user.full_name if user else "",
                "amount": Decimal(amount),
                "is_guaranteed": is_guaranteed,
            }
        )

    return leaderboard
