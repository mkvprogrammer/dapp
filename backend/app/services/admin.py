"""
Бизнес-логика панели администратора (без HTTP-слоя).
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.blockchain import blockchain_service
from app.core.exceptions import UserNotFoundError
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
    await db.commit()
    await db.refresh(user)
    return user

