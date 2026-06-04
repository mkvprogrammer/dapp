"""
P2P-переводы токенов ERC-1155 между студентами.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_helper import write_audit
from app.core.blockchain import blockchain_service
from app.core.exceptions import (
    BlockchainCommunicationError,
    DatabasePersistenceError,
    InsufficientTokensError,
    NotEnrolledInProjectError,
    ProjectNotFoundError,
    UserNotFoundError,
)
from app.core.notify import push_notification
from app.models.notification import NotificationType
from app.models.project import Project
from app.models.transfer import Transfer, TransferStatus
from app.models.user import User
from app.services import project_service

logger = logging.getLogger(__name__)


async def create_transfer(
    db: AsyncSession,
    sender: User,
    *,
    recipient_student_id: str,
    project_id: int,
    amount: Decimal,
    comment: str | None,
    sender_private_key: str,
) -> Transfer:
    recipient_result = await db.execute(
        select(User).where(User.student_id == recipient_student_id.strip())
    )
    recipient = recipient_result.scalar_one_or_none()
    if recipient is None:
        raise UserNotFoundError()

    project = await db.get(Project, project_id)
    if project is None:
        raise ProjectNotFoundError()

    if not await project_service.is_project_participant(db, sender, project):
        raise NotEnrolledInProjectError(
            "Вы не участник этого проекта. Запишитесь по коду на странице «Мои проекты» "
            "или выберите другой проект."
        )
    if not await project_service.is_project_participant(db, recipient, project):
        raise NotEnrolledInProjectError(
            f"Получатель {recipient.student_id} не участник проекта «{project.name}». "
            "Ему нужно вступить по коду приглашения."
        )

    amount_int = int(amount)
    balance = await blockchain_service.get_token_balance(
        sender.wallet_address, project.blockchain_id
    )
    if balance < amount_int:
        raise InsufficientTokensError()

    try:
        tx_hash = await blockchain_service.transfer_tokens_onchain(
            sender_private_key=sender_private_key,
            recipient_wallet=recipient.wallet_address,
            project_blockchain_id=project.blockchain_id,
            amount=amount_int,
        )
    except Exception as exc:
        await db.rollback()
        logger.exception("transfer on-chain failed")
        raise BlockchainCommunicationError() from exc

    transfer = Transfer(
        project_id=project_id,
        sender_id=sender.id,
        recipient_id=recipient.id,
        amount=amount,
        comment=comment,
        status=TransferStatus.COMPLETED.value,
        tx_hash=tx_hash,
    )
    db.add(transfer)

    await push_notification(
        db,
        user_id=recipient.id,
        ntype=NotificationType.TRANSFER_RECEIVED.value,
        title="Входящий перевод",
        body=f"{sender.full_name} отправил {amount} TKN",
        meta={"project_id": project_id, "project_name": project.name},
    )
    await push_notification(
        db,
        user_id=sender.id,
        ntype=NotificationType.TRANSFER_SENT.value,
        title="Исходящий перевод",
        body=f"Вы отправили {amount} TKN пользователю {recipient.student_id}",
        meta={"project_id": project_id},
    )
    await write_audit(
        db,
        event_type="transfer",
        action="token_transfer",
        object_ref=f"project:{project_id} amount:{amount}",
        actor_id=sender.id,
    )

    try:
        await db.commit()
        await db.refresh(transfer)
    except Exception as exc:
        await db.rollback()
        raise DatabasePersistenceError() from exc

    return transfer


async def list_transfers(
    db: AsyncSession,
    user: User,
    *,
    project_id: int | None,
    direction: str,
    limit: int,
    offset: int,
) -> dict:
    q = select(Transfer).order_by(Transfer.created_at.desc())
    if project_id is not None:
        q = q.where(Transfer.project_id == project_id)
    if direction == "in":
        q = q.where(Transfer.recipient_id == user.id)
    elif direction == "out":
        q = q.where(Transfer.sender_id == user.id)
    else:
        q = q.where(or_(Transfer.sender_id == user.id, Transfer.recipient_id == user.id))

    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = await db.execute(q.limit(limit).offset(offset))
    transfers = list(rows.scalars().all())

    user_ids = {t.sender_id for t in transfers} | {t.recipient_id for t in transfers}
    users_map: dict[UUID, User] = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users_map = {u.id: u for u in users_result.scalars().all()}

    items: list[dict] = []
    for t in transfers:
        is_out = t.sender_id == user.id
        counter = users_map[t.recipient_id if is_out else t.sender_id]
        items.append(
            {
                "id": t.id,
                "direction": "out" if is_out else "in",
                "counterparty_name": counter.full_name,
                "counterparty_student_id": counter.student_id,
                "amount": t.amount,
                "comment": t.comment,
                "status": t.status,
                "created_at": t.created_at,
            }
        )
    return {"items": items, "total": int(total or 0)}


async def recent_recipients(db: AsyncSession, user: User, limit: int = 10) -> list[dict]:
    result = await db.execute(
        select(Transfer.recipient_id)
        .where(Transfer.sender_id == user.id)
        .group_by(Transfer.recipient_id)
        .order_by(func.max(Transfer.created_at).desc())
        .limit(limit)
    )
    ids = [row[0] for row in result.all()]
    if not ids:
        return []
    users_result = await db.execute(select(User).where(User.id.in_(ids)))
    users = {u.id: u for u in users_result.scalars().all()}
    return [
        {
            "user_id": uid,
            "student_id": users[uid].student_id,
            "full_name": users[uid].full_name,
        }
        for uid in ids
        if uid in users
    ]
