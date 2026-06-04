"""
Объединяет все ручки в один api_router
Нужен, чтобы не захломлять main.py сотнями импортов
"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.auctions import router as auctions_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.projects import router as projects_router
from app.api.v1.transfers import router as transfers_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.users import router as users_router
from app.api.v1.wallet import router as wallet_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(admin_router)
api_router.include_router(projects_router)
api_router.include_router(auctions_router)
api_router.include_router(attendance_router)
api_router.include_router(users_router)
api_router.include_router(transfers_router)
api_router.include_router(notifications_router)
api_router.include_router(wallet_router)
api_router.include_router(uploads_router)
