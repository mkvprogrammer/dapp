"""
Бизнес-логика управления проектами (без HTTP-слоя).
"""

from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_helper import write_audit
from app.core.blockchain import blockchain_service
from app.core.notify import push_notification
from app.models.notification import NotificationType
from app.core.exceptions import (
    AlreadyEnrolledError,
    BlockchainCommunicationError,
    DatabasePersistenceError,
    ProjectAccessDeniedError,
    ProjectInactiveError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from app.models.auction import Auction, AuctionStatus, Bid, BidStatus
from app.models.project import Project, UserProject
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate

logger = logging.getLogger(__name__)


def _decimal_to_basis_points(rate: Decimal) -> int:
    """Переводит 80.00% в 8000 basis points для смарт-контракта."""
    return int(rate * 100)


async def create_project(
    db: AsyncSession,
    schema: ProjectCreate,
    organizer: User,
    teacher_private_key: str,
) -> tuple[Project, str]:
    """
    Создаёт проект в блокчейне и сохраняет метаданные в PostgreSQL.

    При сбое onchain-транзакции откатывает сессию БД.
    """
    refund_bps = _decimal_to_basis_points(schema.refund_rate)

    try:
        blockchain_id, tx_hash = await blockchain_service.create_project_onchain(
            owner_private_key=teacher_private_key,
            name=schema.name,
            refund_rate_bps=refund_bps,
            penalty_schedule=schema.penalty_schedule,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create project on-chain")
        raise BlockchainCommunicationError() from exc

    # id в БД совпадает с projectId в контракте (см. модель Project)
    join_code = secrets.token_hex(4).upper()

    project = Project(
        id=blockchain_id,
        name=schema.name,
        description=schema.description or "",
        organizer_id=organizer.id,
        blockchain_id=blockchain_id,
        refund_rate=schema.refund_rate,
        penalty_schedule=schema.penalty_schedule,
        initial_supply=schema.initial_supply,
        is_active=True,
        join_code=join_code,
    )

    await write_audit(
        db,
        event_type="token",
        action="create_project",
        object_ref=f"project:{blockchain_id}",
        actor_id=organizer.id,
    )

    try:
        db.add(project)
        await db.commit()
        await db.refresh(project)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist project in database after on-chain success")
        raise DatabasePersistenceError() from exc

    return project, tx_hash


async def enroll_user_in_project(
    db: AsyncSession,
    project_id: int,
    student: User,
) -> tuple[UserProject, str]:
    """Записывает студента на проект и минтит стартовые токены в блокчейне."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise ProjectNotFoundError()
    if not project.is_active:
        raise ProjectInactiveError()

    enrolled_result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == student.id,
            UserProject.project_id == project_id,
        )
    )
    if enrolled_result.scalar_one_or_none() is not None:
        raise AlreadyEnrolledError()

    try:
        tx_hash = await blockchain_service.mint_tokens(
            wallet_address=student.wallet_address,
            blockchain_id=project.blockchain_id,
            amount=project.initial_supply,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to mint tokens on-chain during enrollment")
        raise BlockchainCommunicationError() from exc

    user_project = UserProject(
        user_id=student.id,
        project_id=project_id,
        token_balance=Decimal(project.initial_supply),
    )

    await push_notification(
        db,
        user_id=project.organizer_id,
        ntype=NotificationType.MEMBER_JOINED.value,
        title="Новый участник",
        body=f"{student.full_name} ({student.student_id}) записался на «{project.name}»",
        meta={"project_id": project_id},
    )
    await write_audit(
        db,
        event_type="token",
        action="enroll",
        object_ref=f"project:{project_id} user:{student.id}",
        actor_id=student.id,
    )

    try:
        db.add(user_project)
        await db.commit()
        await db.refresh(user_project)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist enrollment in database after on-chain mint")
        raise DatabasePersistenceError() from exc

    return user_project, tx_hash


async def get_all_projects(db: AsyncSession) -> list[Project]:
    """Возвращает список всех проектов."""
    result = await db.execute(select(Project).order_by(Project.id))
    return list(result.scalars().all())


async def is_project_participant(db: AsyncSession, user: User, project: Project) -> bool:
    """Участник проекта: запись в user_projects или организатор курса."""
    if project.organizer_id == user.id:
        return True
    enrolled = await db.execute(
        select(UserProject).where(
            UserProject.user_id == user.id,
            UserProject.project_id == project.id,
        )
    )
    return enrolled.scalar_one_or_none() is not None


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project:
    """Возвращает проект по ID или выбрасывает ProjectNotFoundError."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError()
    if not project.join_code:
        project.join_code = secrets.token_hex(4).upper()
        await db.commit()
        await db.refresh(project)
    return project


def _assert_organizer_or_admin(actor: User, project: Project) -> None:
    if actor.role == UserRole.ADMIN:
        return
    if actor.role != UserRole.ORGANIZER or project.organizer_id != actor.id:
        raise ProjectAccessDeniedError()


async def get_project_members(
    db: AsyncSession,
    project_id: int,
    actor: User,
) -> list[dict]:
    project = await get_project_by_id(db, project_id)
    _assert_organizer_or_admin(actor, project)

    result = await db.execute(
        select(UserProject, User)
        .join(User, User.id == UserProject.user_id)
        .where(UserProject.project_id == project_id)
        .order_by(User.student_id)
    )
    members: list[dict] = []
    for enrollment, user in result.all():
        onchain_balance = await blockchain_service.get_token_balance(
            user.wallet_address,
            project.blockchain_id,
        )
        members.append(
            {
                "user_id": user.id,
                "student_id": user.student_id,
                "full_name": user.full_name,
                "wallet_address": user.wallet_address,
                "token_balance": Decimal(onchain_balance),
                "enrolled_at": enrollment.enrolled_at,
            }
        )
    return members


async def mint_tokens_for_member(
    db: AsyncSession,
    project_id: int,
    target_user_id,
    amount: int,
    actor: User,
) -> tuple[UserProject, str]:
    from uuid import UUID

    project = await get_project_by_id(db, project_id)
    _assert_organizer_or_admin(actor, project)

    user_result = await db.execute(select(User).where(User.id == UUID(str(target_user_id))))
    target = user_result.scalar_one_or_none()
    if target is None:
        raise UserNotFoundError()

    enroll_result = await db.execute(
        select(UserProject).where(
            UserProject.project_id == project_id,
            UserProject.user_id == target.id,
        )
    )
    enrollment = enroll_result.scalar_one_or_none()
    if enrollment is None:
        raise UserNotFoundError()

    try:
        tx_hash = await blockchain_service.mint_tokens(
            wallet_address=target.wallet_address,
            blockchain_id=project.blockchain_id,
            amount=amount,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to mint tokens for member")
        raise BlockchainCommunicationError() from exc

    enrollment.token_balance += Decimal(amount)
    try:
        await db.commit()
        await db.refresh(enrollment)
    except Exception as exc:
        await db.rollback()
        raise DatabasePersistenceError() from exc

    return enrollment, tx_hash


async def get_user_projects(db: AsyncSession, user: User) -> list[dict]:
    """Проекты, на которые записан текущий пользователь."""
    result = await db.execute(
        select(Project, UserProject)
        .join(UserProject, UserProject.project_id == Project.id)
        .where(UserProject.user_id == user.id)
        .order_by(Project.id)
    )
    items: list[dict] = []
    for project, enrollment in result.all():
        balance = await blockchain_service.get_token_balance(
            user.wallet_address,
            project.blockchain_id,
        )
        items.append(
            {
                "id": project.id,
                "name": project.name,
                "organizer_id": project.organizer_id,
                "is_active": project.is_active,
                "token_balance": Decimal(balance),
                "enrolled_at": enrollment.enrolled_at,
            }
        )
    return items


async def join_project_by_code(
    db: AsyncSession,
    student: User,
    code: str,
) -> tuple[UserProject, Project, str | None]:
    """Запись на проект по коду приглашения."""
    normalized = code.strip().upper()
    result = await db.execute(select(Project).where(Project.join_code == normalized))
    project = result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError()
    user_project, tx_hash = await enroll_user_in_project(db, project.id, student)
    return user_project, project, tx_hash


async def get_project_balance_for_user(
    db: AsyncSession,
    project_id: int,
    user: User,
) -> dict:
    project = await get_project_by_id(db, project_id)
    available = Decimal(
        await blockchain_service.get_token_balance(user.wallet_address, project.blockchain_id)
    )
    frozen_result = await db.execute(
        select(func.coalesce(func.sum(Bid.amount), 0)).where(
            Bid.user_id == user.id,
            Bid.status == BidStatus.LOCKED,
            Bid.auction_id.in_(select(Auction.id).where(Auction.project_id == project_id)),
        )
    )
    frozen = Decimal(frozen_result.scalar() or 0)
    return {
        "project_id": project_id,
        "available": available,
        "frozen": frozen,
        "pending_refund": Decimal(0),
    }


async def get_organizer_stats(db: AsyncSession, project_id: int, actor: User) -> dict:
    from datetime import UTC, datetime, timedelta

    project = await get_project_by_id(db, project_id)
    _assert_organizer_or_admin(actor, project)
    now = datetime.now(UTC)
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)

    members_count = await db.scalar(
        select(func.count(UserProject.id)).where(UserProject.project_id == project_id)
    )
    members_month_ago = await db.scalar(
        select(func.count(UserProject.id)).where(
            UserProject.project_id == project_id,
            UserProject.enrolled_at < month_ago,
        )
    )
    open_auctions = await db.scalar(
        select(func.count(Auction.id)).where(
            Auction.project_id == project_id,
            Auction.status == AuctionStatus.OPEN,
        )
    )
    circulation = Decimal(0)
    members = await get_project_members(db, project_id, actor)
    for m in members:
        circulation += m["token_balance"]

    att_stats = await get_attendance_stats(db, project_id, actor)

    weekly_mints: list[dict] = []
    auction_activity_by_day: list[dict] = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        enrolls = await db.scalar(
            select(func.count(UserProject.id)).where(
                UserProject.project_id == project_id,
                UserProject.enrolled_at >= day_start,
                UserProject.enrolled_at < day_end,
            )
        )
        auctions_created = await db.scalar(
            select(func.count(Auction.id)).where(
                Auction.project_id == project_id,
                Auction.created_at >= day_start,
                Auction.created_at < day_end,
            )
        )
        label = day.strftime("%d.%m")
        weekly_mints.append({"date": label, "count": int(enrolls or 0)})
        auction_activity_by_day.append({"date": label, "count": int(auctions_created or 0)})

    return {
        "project_id": project.id,
        "project_name": project.name,
        "semester_label": None,
        "members_count": int(members_count or 0),
        "members_trend_month": int(members_count or 0) - int(members_month_ago or 0),
        "tokens_in_circulation": circulation,
        "tokens_trend_week": circulation,
        "active_auctions_count": int(open_auctions or 0),
        "average_attendance_percent": att_stats["average_attendance_percent"],
        "attendance_trend_month": att_stats["average_attendance_percent"],
        "weekly_mints": weekly_mints,
        "auction_activity_by_day": auction_activity_by_day,
    }


async def get_attendance_stats(db: AsyncSession, project_id: int, user: User) -> dict:
    await get_project_by_id(db, project_id)
    total_bids = await db.scalar(
        select(func.count(Bid.id))
        .join(Auction, Auction.id == Bid.auction_id)
        .where(Auction.project_id == project_id)
    )
    confirmed = await db.scalar(
        select(func.count(Bid.id))
        .join(Auction, Auction.id == Bid.auction_id)
        .where(
            Auction.project_id == project_id,
            Bid.status == BidStatus.REFUNDED,
        )
    )
    pct = int((confirmed or 0) * 100 / max(1, total_bids or 1))
    my_visits = None
    if user.role.value == "student":
        my_visits = await db.scalar(
            select(func.count(Bid.id))
            .join(Auction, Auction.id == Bid.auction_id)
            .where(
                Auction.project_id == project_id,
                Bid.user_id == user.id,
                Bid.status == BidStatus.REFUNDED,
            )
        )
    return {
        "project_id": project_id,
        "average_attendance_percent": pct,
        "total_sessions": int(total_bids or 0),
        "my_visits": int(my_visits) if my_visits is not None else None,
    }
