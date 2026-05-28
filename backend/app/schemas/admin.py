"""
Схемы панели администратора.
"""

from pydantic import BaseModel

from app.models.user import UserRole


class ChangeRoleRequest(BaseModel):
    """Запрос на смену роли пользователя."""

    new_role: UserRole

