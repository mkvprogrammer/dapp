from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import settings
from app.core.exceptions import ProjectNotFoundError
from app.models.user import User
from app.schemas.transfer import WalletBalanceResponse
from app.services import project_service, user_service
from app.core.blockchain import blockchain_service
from app.models.project import UserProject
from sqlalchemy import select
from database import get_db

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/balance", response_model=WalletBalanceResponse)
async def wallet_balance(
    project_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletBalanceResponse:
    if project_id is not None:
        bal = await project_service.get_project_balance_for_user(db, project_id, current_user)
        return WalletBalanceResponse(available=bal["available"], project_id=project_id)
    totals = await user_service.get_balances(db, current_user)
    return WalletBalanceResponse(available=totals["available"], project_id=None)


@router.post("/demo-top-up")
async def demo_top_up(
    project_id: int = Query(...),
    amount: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.debug and not settings.allow_demo_topup:
        from fastapi import HTTPException
        raise HTTPException(403, "Demo top-up отключён")
    project = await project_service.get_project_by_id(db, project_id)
    enrolled = await db.execute(
        select(UserProject).where(
            UserProject.user_id == current_user.id,
            UserProject.project_id == project_id,
        )
    )
    ep = enrolled.scalar_one_or_none()
    if ep is None:
        raise ProjectNotFoundError()
    tx = await blockchain_service.mint_tokens(
        current_user.wallet_address, project.blockchain_id, amount
    )
    from decimal import Decimal
    ep.token_balance += Decimal(amount)
    await db.commit()
    return {"new_balance": str(ep.token_balance), "tx_hash": tx}
