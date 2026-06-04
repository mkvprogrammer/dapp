"""Запись в журнал аудита."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    event_type: str,
    action: str,
    object_ref: str,
    actor_id: UUID | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    row = AuditLog(
        event_type=event_type,
        actor_id=actor_id,
        action=action,
        object_ref=object_ref,
        ip_address=ip_address,
    )
    db.add(row)
    await db.flush()
    return row
