"""
Бизнес-логика управления проектами (без HTTP-слоя).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.blockchain import blockchain_service
from app.core.exceptions import (
    AlreadyEnrolledError,
    BlockchainCommunicationError,
    DatabasePersistenceError,
    ProjectInactiveError,
    ProjectNotFoundError,
)
from app.models.project import Project, UserProject
from app.models.user import User
from app.schemas.project import ProjectCreate

logger = logging.getLogger(__name__)


def _decimal_to_basis_points(rate: Decimal) -> int:
    """Переводит 80.00% в 8000 basis points для смарт-контракта."""
    return int(rate * 100)


async def create_project(
    db: AsyncSession,
    schema: ProjectCreate,
    organizer: User,
    teacher_private_key: str,
) -> tuple[Project, str]:
    """
    Создаёт проект в блокчейне и сохраняет метаданные в PostgreSQL.

    При сбое onchain-транзакции откатывает сессию БД.
    """
    refund_bps = _decimal_to_basis_points(schema.refund_rate)

    try:
        blockchain_id, tx_hash = await blockchain_service.create_project_onchain(
            owner_private_key=teacher_private_key,
            name=schema.name,
            refund_rate_bps=refund_bps,
            penalty_schedule=schema.penalty_schedule,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to create project on-chain")
        raise BlockchainCommunicationError() from exc

    # id в БД совпадает с projectId в контракте (см. модель Project)
    project = Project(
        id=blockchain_id,
        name=schema.name,
        description=schema.description or "",
        organizer_id=organizer.id,
        blockchain_id=blockchain_id,
        refund_rate=schema.refund_rate,
        penalty_schedule=schema.penalty_schedule,
        initial_supply=schema.initial_supply,
        is_active=True,
    )

    try:
        db.add(project)
        await db.commit()
        await db.refresh(project)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist project in database after on-chain success")
        raise DatabasePersistenceError() from exc

    return project, tx_hash


async def enroll_user_in_project(
    db: AsyncSession,
    project_id: int,
    student: User,
) -> tuple[UserProject, str]:
    """Записывает студента на проект и минтит стартовые токены в блокчейне."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise ProjectNotFoundError()
    if not project.is_active:
        raise ProjectInactiveError()

    enrolled_result = await db.execute(
        select(UserProject).where(
            UserProject.user_id == student.id,
            UserProject.project_id == project_id,
        )
    )
    if enrolled_result.scalar_one_or_none() is not None:
        raise AlreadyEnrolledError()

    try:
        tx_hash = await blockchain_service.mint_tokens(
            wallet_address=student.wallet_address,
            blockchain_id=project.blockchain_id,
            amount=project.initial_supply,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to mint tokens on-chain during enrollment")
        raise BlockchainCommunicationError() from exc

    user_project = UserProject(
        user_id=student.id,
        project_id=project_id,
        token_balance=Decimal(project.initial_supply),
    )

    try:
        db.add(user_project)
        await db.commit()
        await db.refresh(user_project)
    except Exception as exc:
        await db.rollback()
        logger.exception("Failed to persist enrollment in database after on-chain mint")
        raise DatabasePersistenceError() from exc

    return user_project, tx_hash


async def get_all_projects(db: AsyncSession) -> list[Project]:
    """Возвращает список всех проектов."""
    result = await db.execute(select(Project).order_by(Project.id))
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project:
    """Возвращает проект по ID или выбрасывает ProjectNotFoundError."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise ProjectNotFoundError()
    return project
