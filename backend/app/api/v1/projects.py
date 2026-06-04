"""
HTTP-ручки управления проектами.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.project import (
    AttendanceStatsResponse,
    EnrollResponse,
    MintTokensRequest,
    MintTokensResponse,
    OrganizerStatsResponse,
    ProjectBalanceResponse,
    ProjectCreate,
    ProjectCreatedResponse,
    ProjectDetailResponse,
    ProjectJoinByCodeRequest,
    ProjectJoinByCodeResponse,
    ProjectListResponse,
    ProjectMemberResponse,
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


@router.post("/join-by-code", response_model=ProjectJoinByCodeResponse)
async def join_by_code(
    payload: ProjectJoinByCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.STUDENT])),
) -> ProjectJoinByCodeResponse:
    enrollment, project, tx_hash = await project_service.join_project_by_code(
        db, current_user, payload.code
    )
    return ProjectJoinByCodeResponse(
        project_id=project.id,
        project_name=project.name,
        token_balance=enrollment.token_balance,
        enrolled_at=enrollment.enrolled_at,
        tx_hash=tx_hash,
    )


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
        join_code=project.join_code,
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


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def list_project_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER, UserRole.ADMIN])),
) -> list[ProjectMemberResponse]:
    """Участники проекта с балансом токенов (для панели организатора)."""
    members = await project_service.get_project_members(db, project_id, current_user)
    return [ProjectMemberResponse(**m) for m in members]


@router.post(
    "/{project_id}/members/{user_id}/mint-tokens",
    response_model=MintTokensResponse,
    status_code=status.HTTP_200_OK,
)
async def mint_tokens_for_member(
    project_id: int,
    user_id: UUID,
    payload: MintTokensRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER, UserRole.ADMIN])),
) -> MintTokensResponse:
    """Начисление токенов участнику проекта (onchain mint)."""
    enrollment, tx_hash = await project_service.mint_tokens_for_member(
        db=db,
        project_id=project_id,
        target_user_id=user_id,
        amount=payload.amount,
        actor=current_user,
    )
    return MintTokensResponse(
        user_id=enrollment.user_id,
        project_id=project_id,
        amount=payload.amount,
        new_balance=enrollment.token_balance,
        tx_hash=tx_hash,
    )


@router.get("/{project_id}/balance", response_model=ProjectBalanceResponse)
async def project_balance(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectBalanceResponse:
    data = await project_service.get_project_balance_for_user(db, project_id, current_user)
    return ProjectBalanceResponse(**data)


@router.get("/{project_id}/organizer/stats", response_model=OrganizerStatsResponse)
async def organizer_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER, UserRole.ADMIN])),
) -> OrganizerStatsResponse:
    data = await project_service.get_organizer_stats(db, project_id, current_user)
    return OrganizerStatsResponse(**data)


@router.get("/{project_id}/attendance/stats", response_model=AttendanceStatsResponse)
async def attendance_stats(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttendanceStatsResponse:
    data = await project_service.get_attendance_stats(db, project_id, current_user)
    return AttendanceStatsResponse(**data)
