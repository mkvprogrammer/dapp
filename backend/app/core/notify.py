"""Создание in-app уведомлений."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def push_notification(
    db: AsyncSession,
    *,
    user_id: UUID,
    ntype: str,
    title: str,
    body: str,
    meta: dict | None = None,
) -> Notification:
    row = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        body=body,
        meta=meta or {},
    )
    db.add(row)
    await db.flush()
    return row
