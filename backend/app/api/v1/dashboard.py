from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service
from database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    data = await dashboard_service.get_dashboard(db, current_user)
    return DashboardResponse(**data)
