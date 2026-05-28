"""
HTTP-ручки управления проектами.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.project import (
    EnrollResponse,
    ProjectCreate,
    ProjectCreatedResponse,
    ProjectDetailResponse,
    ProjectListResponse,
)
from app.services import project_service
from database import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectListResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectListResponse]:
    """Список всех проектов (доступен любому авторизованному пользователю)."""
    projects = await project_service.get_all_projects(db)
    return [ProjectListResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectDetailResponse:
    """Детальная информация о проекте."""
    project = await project_service.get_project_by_id(db, project_id)
    return ProjectDetailResponse.model_validate(project)


@router.post("/", response_model=ProjectCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER])),
) -> ProjectCreatedResponse:
    """Создание проекта организатором."""
    teacher_private_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )

    project, tx_hash = await project_service.create_project(
        db=db,
        schema=payload,
        organizer=current_user,
        teacher_private_key=teacher_private_key,
    )

    return ProjectCreatedResponse(
        id=project.id,
        name=project.name,
        blockchain_id=project.blockchain_id,
        tx_hash=tx_hash,
    )


@router.post("/{project_id}/enroll", response_model=EnrollResponse)
async def enroll_in_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.STUDENT])),
) -> EnrollResponse:
    """Запись студента на проект."""
    user_project, tx_hash = await project_service.enroll_user_in_project(
        db=db,
        project_id=project_id,
        student=current_user,
    )

    return EnrollResponse(
        user_id=user_project.user_id,
        project_id=user_project.project_id,
        enrolled_at=user_project.enrolled_at,
        token_balance=user_project.token_balance,
        tx_hash=tx_hash,
    )
