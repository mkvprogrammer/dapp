"""
Посещаемость на аукционе: подтверждение преподавателем (без кодов).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.attendance import (
    AttendanceEntry,
    AttendanceListResponse,
    AttendanceStudentRequest,
    AttendanceTxResponse,
    OrganizerActionRequest,
)
from app.services import attendance_service
from database import get_db

router = APIRouter(prefix="/auctions", tags=["Attendance"])


@router.get("/{auction_id}/attendance", response_model=AttendanceListResponse)
async def list_auction_attendance(
    auction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER])),
) -> AttendanceListResponse:
    """Список участников со ставками и статусом посещения."""
    auction, entries = await attendance_service.list_attendance(db, auction_id, current_user)
    return AttendanceListResponse(
        auction_id=auction.id,
        resource_name=auction.resource_name,
        lesson_start_time=auction.lesson_start_time.isoformat(),
        entries=[AttendanceEntry(**row) for row in entries],
    )


@router.post(
    "/{auction_id}/attendance/confirm",
    response_model=AttendanceTxResponse,
    status_code=status.HTTP_200_OK,
)
async def confirm_student_attendance(
    auction_id: int,
    payload: AttendanceStudentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER])),
) -> AttendanceTxResponse:
    """Преподаватель подтверждает присутствие студента (возврат по ставке)."""
    organizer_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    tx_hash, sid = await attendance_service.confirm_presence(
        db=db,
        auction_id=auction_id,
        student_id=payload.student_id.strip(),
        organizer=current_user,
        organizer_private_key=organizer_key,
    )
    return AttendanceTxResponse(
        auction_id=auction_id,
        student_id=sid,
        tx_hash=tx_hash,
        message="Присутствие подтверждено, возврат выполнен в блокчейне",
    )


@router.post(
    "/{auction_id}/attendance/mark-absent",
    response_model=AttendanceTxResponse,
)
async def mark_student_absent(
    auction_id: int,
    payload: AttendanceStudentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER])),
) -> AttendanceTxResponse:
    """Преподаватель отмечает прогул (штраф при закрытии дня)."""
    organizer_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    tx_hash, sid = await attendance_service.mark_student_absent(
        db=db,
        auction_id=auction_id,
        student_id=payload.student_id.strip(),
        organizer=current_user,
        organizer_private_key=organizer_key,
    )
    return AttendanceTxResponse(
        auction_id=auction_id,
        student_id=sid,
        tx_hash=tx_hash,
        message="Студент отмечен как отсутствующий",
    )


@router.post(
    "/{auction_id}/attendance/close-day",
    response_model=AttendanceTxResponse,
)
async def close_auction_day(
    auction_id: int,
    payload: OrganizerActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.ORGANIZER])),
) -> AttendanceTxResponse:
    """Закрытие дня: возврат оставшимся, штраф прогульщикам."""
    organizer_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key,
        payload.password,
    )
    tx_hash = await attendance_service.close_lesson_day(
        db=db,
        auction_id=auction_id,
        organizer=current_user,
        organizer_private_key=organizer_key,
    )
    return AttendanceTxResponse(
        auction_id=auction_id,
        tx_hash=tx_hash,
        message="День закрыт: возвраты и штрафы обработаны в блокчейне",
    )
