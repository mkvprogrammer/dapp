from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
)
from app.services import notification_service
from database import get_db

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    type: str | None = None,
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    data = await notification_service.list_notifications(
        db,
        current_user.id,
        ntype=type,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=[
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "body": n.body,
                "meta": n.meta or {},
                "is_read": n.is_read,
                "created_at": n.created_at,
            }
            for n in data["items"]
        ],
        total=data["total"],
        unread_count=data["unread_count"],
    )


@router.patch("/read-all", response_model=NotificationReadAllResponse)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadAllResponse:
    count = await notification_service.mark_all_read(db, current_user.id)
    return NotificationReadAllResponse(updated_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationReadResponse)
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadResponse:
    row = await notification_service.mark_read(db, current_user.id, notification_id)
    return NotificationReadResponse(id=row.id, is_read=row.is_read)
