"""
HTTP-ручки P2P-переводов токенов между участниками проекта.
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import RoleChecker, get_current_user
from app.core.crypto import decrypt_wallet_private_key
from app.models.user import User, UserRole
from app.schemas.transfer import (
    RecentRecipientsResponse,
    TransferCreate,
    TransferListResponse,
    TransferResponse,
)
from app.services import transfer_service
from database import get_db

router = APIRouter(prefix="/transfers", tags=["Transfers"])


@router.post("", response_model=TransferResponse, status_code=201)
async def create_transfer(
    payload: TransferCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RoleChecker([UserRole.STUDENT, UserRole.ORGANIZER])),
) -> TransferResponse:
    """Перевод токенов ERC-1155 другому участнику того же проекта."""
    sender_key = decrypt_wallet_private_key(
        current_user.encrypted_private_key, payload.password
    )
    transfer = await transfer_service.create_transfer(
        db,
        current_user,
        recipient_student_id=payload.recipient_student_id.strip(),
        project_id=payload.project_id,
        amount=payload.amount,
        comment=payload.comment,
        sender_private_key=sender_key,
    )
    recipient = await db.get(User, transfer.recipient_id)
    sender = current_user
    return TransferResponse(
        id=transfer.id,
        project_id=transfer.project_id,
        sender_student_id=sender.student_id,
        recipient_student_id=recipient.student_id,
        recipient_full_name=recipient.full_name,
        amount=transfer.amount,
        comment=transfer.comment,
        status=transfer.status,
        tx_hash=transfer.tx_hash,
        created_at=transfer.created_at,
    )


@router.get("", response_model=TransferListResponse)
async def list_transfers(
    project_id: int | None = None,
    direction: str = Query("all", pattern="^(all|in|out)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransferListResponse:
    """История входящих и исходящих переводов с пагинацией."""
    data = await transfer_service.list_transfers(
        db, current_user, project_id=project_id, direction=direction, limit=limit, offset=offset
    )
    return TransferListResponse(**data)


@router.get("/recent-recipients", response_model=RecentRecipientsResponse)
async def recent_recipients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecentRecipientsResponse:
    """Недавние получатели переводов для быстрого выбора в UI."""
    items = await transfer_service.recent_recipients(db, current_user)
    return RecentRecipientsResponse(items=items)


@router.get("/export")
async def export_transfers_csv(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Экспорт истории переводов текущего пользователя в CSV."""
    data = await transfer_service.list_transfers(
        db, current_user, project_id=None, direction="all", limit=1000, offset=0
    )
    lines = ["direction,counterparty,amount,status,created_at"]
    for item in data["items"]:
        lines.append(
            f"{item['direction']},{item['counterparty_student_id']},{item['amount']},{item['status']},{item['created_at'].isoformat()}"
        )
    body = "\n".join(lines)
    return StreamingResponse(
        iter([body]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transfers.csv"},
    )
