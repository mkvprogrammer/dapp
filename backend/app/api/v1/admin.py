"""
HTTP-ручки панели администратора (тонкий слой над app.services.admin).
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminHealthResponse,
    AdminUserListItem,
    AdminUserListResponse,
    AuditLogResponse,
    ChangeRoleRequest,
    EmergencyStopRequest,
    EmergencyStopResponse,
    ServiceHealth,
)
from app.schemas.auth import UserResponse
from app.services import admin as admin_service
from database import get_db

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    search: str | None = None,
    role: UserRole | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> AdminUserListResponse:
    """Список пользователей с поиском, фильтром по роли и пагинацией."""
    data = await admin_service.list_users_paginated(
        db, search=search, role=role, limit=limit, offset=offset
    )
    return AdminUserListResponse(
        items=[AdminUserListItem.model_validate(u) for u in data["items"]],
        total=data["total"],
    )


@router.get("/audit-log", response_model=AuditLogResponse)
async def audit_log(
    event_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> AuditLogResponse:
    """Журнал аудита: действия пользователей и системные события."""
    data = await admin_service.list_audit_log(
        db, event_type=event_type, limit=limit, offset=offset
    )
    from app.schemas.admin import AuditLogEntry
    return AuditLogResponse(
        items=[AuditLogEntry(**i) for i in data["items"]],
        total=data["total"],
    )


@router.post("/emergency-stop", response_model=EmergencyStopResponse)
async def emergency_stop(
    payload: EmergencyStopRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> EmergencyStopResponse:
    """Экстренная остановка всех открытых аукционов (только в БД, без onchain)."""
    count = await admin_service.emergency_stop_auctions(db, current_user, payload.reason)
    return EmergencyStopResponse(
        stopped_auctions_count=count,
        message=f"Остановлено аукционов в БД: {count}",
    )


@router.get("/health", response_model=AdminHealthResponse)
async def admin_health(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> AdminHealthResponse:
    """Сводка здоровья стека: PostgreSQL, блокчейн, метрики аукционов."""
    data = await admin_service.get_admin_health(db)
    return AdminHealthResponse(
        services=[ServiceHealth(**s) for s in data["services"]],
        active_auctions=data["active_auctions"],
        bids_per_hour=data["bids_per_hour"],
        blockchain_block_number=data["blockchain_block_number"],
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_role(
    user_id: UUID,
    payload: ChangeRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
) -> UserResponse:
    """
    Меняет роль пользователя.

    Доступ только для администраторов (RoleChecker).
    """
    user = await admin_service.update_user_role(db, user_id=user_id, new_role=payload.new_role)
    return UserResponse.model_validate(user)

