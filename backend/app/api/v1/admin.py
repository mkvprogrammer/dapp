"""
HTTP-ручки панели администратора (тонкий слой над app.services.admin).
"""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker
from app.models.user import User, UserRole
from app.schemas.admin import ChangeRoleRequest
from app.schemas.auth import UserResponse
from app.services import admin as admin_service
from database import get_db

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


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

