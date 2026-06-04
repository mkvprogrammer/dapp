"""
Бизнес-логика панели администратора (без HTTP-слоя).
"""

import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_helper import write_audit
from app.core.blockchain import blockchain_service
from app.core.exceptions import UserNotFoundError
from app.models.auction import Auction, AuctionStatus, Bid
from app.models.audit import AuditLog
from app.models.user import User, UserRole


async def update_user_role(db: AsyncSession, user_id: UUID, new_role: UserRole) -> User:
    """
    Меняет роль пользователя в БД и, при необходимости, синхронизирует роль в блокчейне.

    Важно: сервис не знает про HTTP и не выбрасывает HTTPException.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UserNotFoundError()

    old_role = user.role
    if old_role == new_role:
        return user

    # Синхронизируем роли во всех контрактах.
    if new_role == UserRole.ORGANIZER:
        await blockchain_service.sync_roles_for_user(user.wallet_address, target="organizer")
    elif new_role == UserRole.STUDENT:
        await blockchain_service.sync_roles_for_user(user.wallet_address, target="user")
    else:
        # Для ADMIN (и любых будущих ролей) onchain-роль не задаём по умолчанию.
        await blockchain_service.sync_roles_for_user(user.wallet_address, target="none")

    user.role = new_role
    await write_audit(
        db,
        event_type="user",
        action=f"role_change:{old_role.value}->{new_role.value}",
        object_ref=f"user:{user_id}",
        actor_id=None,
    )
    await db.commit()
    await db.refresh(user)
    return user


async def list_users(db: AsyncSession, search: str | None = None) -> list[User]:
    query = select(User).order_by(User.student_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(
            (User.student_id.ilike(pattern)) | (User.full_name.ilike(pattern))
        )
    result = await db.execute(query)
    return list(result.scalars().all())


async def list_users_paginated(
    db: AsyncSession,
    *,
    search: str | None,
    role: UserRole | None,
    limit: int,
    offset: int,
) -> dict:
    q = select(User)
    if search:
        pattern = f"%{search.strip()}%"
        q = q.where((User.student_id.ilike(pattern)) | (User.full_name.ilike(pattern)))
    if role:
        q = q.where(User.role == role)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = await db.execute(q.order_by(User.student_id).limit(limit).offset(offset))
    return {"items": list(rows.scalars().all()), "total": int(total or 0)}


async def list_audit_log(
    db: AsyncSession,
    *,
    event_type: str | None,
    limit: int,
    offset: int,
) -> dict:
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if event_type:
        q = q.where(AuditLog.event_type == event_type)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = await db.execute(q.limit(limit).offset(offset))
    logs = list(rows.scalars().all())
    actor_ids = {log.actor_id for log in logs if log.actor_id}
    actors: dict[UUID, User] = {}
    if actor_ids:
        ar = await db.execute(select(User).where(User.id.in_(actor_ids)))
        actors = {u.id: u for u in ar.scalars().all()}
    items = []
    for log in logs:
        actor = actors.get(log.actor_id) if log.actor_id else None
        items.append(
            {
                "id": log.id,
                "created_at": log.created_at,
                "actor_name": actor.full_name if actor else "Система",
                "actor_student_id": actor.student_id if actor else None,
                "action": log.action,
                "object_ref": log.object_ref,
                "ip_address": log.ip_address,
            }
        )
    return {"items": items, "total": int(total or 0)}


async def emergency_stop_auctions(db: AsyncSession, actor: User, reason: str) -> int:
    now = datetime.now(UTC)
    result = await db.execute(
        select(Auction).where(
            Auction.status == AuctionStatus.OPEN,
            Auction.end_time > now,
        )
    )
    auctions = list(result.scalars().all())
    for auction in auctions:
        auction.status = AuctionStatus.CANCELLED
    await write_audit(
        db,
        event_type="system",
        action=f"emergency_stop: {reason}",
        object_ref=f"auctions:{len(auctions)}",
        actor_id=actor.id,
    )
    await db.commit()
    return len(auctions)


async def get_admin_health(db: AsyncSession) -> dict:
    t0 = time.perf_counter()
    try:
        await db.execute(select(func.count(User.id)))
        db_ms = int((time.perf_counter() - t0) * 1000)
        db_status = "ok"
        db_detail = "PostgreSQL connected"
    except Exception as exc:
        db_ms = None
        db_status = "error"
        db_detail = str(exc)

    bc_status = "ok"
    bc_detail = "PoA node"
    block_number = None
    try:
        block_number = await blockchain_service.get_block_number()
    except Exception as exc:
        bc_status = "error"
        bc_detail = str(exc)

    hour_ago = datetime.now(UTC) - timedelta(hours=1)
    bids_hour = await db.scalar(
        select(func.count(Bid.id)).where(Bid.created_at >= hour_ago)
    )
    active = await db.scalar(
        select(func.count(Auction.id)).where(Auction.status == AuctionStatus.OPEN)
    )
    return {
        "services": [
            {"name": "PostgreSQL", "status": db_status, "detail": db_detail, "latency_ms": db_ms},
            {"name": "Blockchain", "status": bc_status, "detail": bc_detail, "latency_ms": None},
        ],
        "active_auctions": int(active or 0),
        "bids_per_hour": int(bids_hour or 0),
        "blockchain_block_number": block_number,
    }

