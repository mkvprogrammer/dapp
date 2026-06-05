"""
HTTP-ручки профиля, балансов и активности текущего пользователя.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.project import MyProjectResponse
from app.schemas.user import (
    ActivityListResponse,
    MyActiveAuctionsResponse,
    UserBalancesResponse,
    UserProfileResponse,
    UserProfileUpdate,
    UserStatsResponse,
)
from app.services import project_service, user_service
from database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/projects", response_model=list[MyProjectResponse])
async def list_my_projects(
    search: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MyProjectResponse]:
    """Проекты, на которые записан текущий пользователь, с onchain-балансом."""
    rows = await project_service.get_user_projects(db, current_user)
    if is_active is not None:
        rows = [r for r in rows if r["is_active"] == is_active]
    if search:
        q = search.lower()
        rows = [r for r in rows if q in r["name"].lower()]
    return [MyProjectResponse(**row) for row in rows]


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Профиль и агрегированная статистика текущего пользователя."""
    data = await user_service.get_profile(db, current_user)
    return UserProfileResponse(
        user_id=current_user.id,
        student_id=current_user.student_id,
        full_name=current_user.full_name,
        faculty=current_user.faculty,
        wallet_address=current_user.wallet_address,
        role=current_user.role.value,
        stats=UserStatsResponse(**data["stats"]),
        created_at=current_user.created_at,
    )


@router.patch("/me/profile", response_model=UserProfileResponse)
async def patch_my_profile(
    payload: UserProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Частичное обновление ФИО и факультета в профиле."""
    user = await user_service.update_profile(
        db,
        current_user,
        full_name=payload.full_name,
        faculty=payload.faculty,
    )
    data = await user_service.get_profile(db, user)
    return UserProfileResponse(
        user_id=user.id,
        student_id=user.student_id,
        full_name=user.full_name,
        faculty=user.faculty,
        wallet_address=user.wallet_address,
        role=user.role.value,
        stats=UserStatsResponse(**data["stats"]),
        created_at=user.created_at,
    )


@router.get("/me/balances", response_model=UserBalancesResponse)
async def get_my_balances(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserBalancesResponse:
    """Сводный и помесячный баланс токенов по всем проектам пользователя."""
    data = await user_service.get_balances(db, current_user)
    return UserBalancesResponse(**data)


@router.get("/me/activity", response_model=ActivityListResponse)
async def get_my_activity(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivityListResponse:
    """Лента активности: ставки на аукционах и переводы токенов."""
    data = await user_service.get_activity(db, current_user, limit=limit, offset=offset)
    return ActivityListResponse(**data)


@router.get("/me/auctions/active", response_model=MyActiveAuctionsResponse)
async def get_my_active_auctions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MyActiveAuctionsResponse:
    """Открытые аукционы, в которых у пользователя есть активная ставка."""
    items = await user_service.get_active_auctions(db, current_user)
    return MyActiveAuctionsResponse(items=items)
