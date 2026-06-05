"""
In-app уведомления.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.models.notification import Notification


async def list_notifications(
    db: AsyncSession,
    user_id: UUID,
    *,
    ntype: str | None,
    unread_only: bool,
    limit: int,
    offset: int,
) -> dict:
    """Список уведомлений пользователя с подсчётом непрочитанных."""
    q = select(Notification).where(Notification.user_id == user_id)
    if ntype:
        q = q.where(Notification.type == ntype)
    if unread_only:
        q = q.where(Notification.is_read.is_(False))
    q = q.order_by(Notification.created_at.desc())

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    unread = await db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )
    rows = await db.execute(q.limit(limit).offset(offset))
    items = list(rows.scalars().all())
    return {"items": items, "total": int(total or 0), "unread_count": int(unread or 0)}


async def mark_read(db: AsyncSession, user_id: UUID, notification_id: UUID) -> Notification:
    """Помечает одно уведомление прочитанным (только своё)."""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise UserNotFoundError()
    row.is_read = True
    await db.commit()
    await db.refresh(row)
    return row


async def mark_all_read(db: AsyncSession, user_id: UUID) -> int:
    """Помечает все непрочитанные уведомления пользователя прочитанными."""
    result = await db.execute(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
    )
    rows = list(result.scalars().all())
    for row in rows:
        row.is_read = True
    await db.commit()
    return len(rows)
