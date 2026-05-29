"""
Объединяет все ручки в один api_router
Нужен, чтобы не захломлять main.py сотнями импортов
"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.auctions import router as auctions_router
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(projects_router)
api_router.include_router(auctions_router)
