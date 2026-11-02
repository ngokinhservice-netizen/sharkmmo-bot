from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import PaymentTransaction
from backend.app.payments.payment_service import payment_service

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("", dependencies=[Depends(verify_admin_key)])
async def list_payments(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(PaymentTransaction)
    if status:
        q = q.where(PaymentTransaction.status == status)

    q = q.order_by(PaymentTransaction.id.desc()).offset(offset).limit(limit)
    res = await session.execute(q)
    txs = res.scalars().all()

    return {"success": True, "count": len(txs), "transactions": txs}


@router.post("/{id}/approve", dependencies=[Depends(verify_admin_key)])
async def approve_payment(id: int, session: AsyncSession = Depends(get_db_session)):
    res = await payment_service.confirm_payment(
        session=session,
        transaction_id=id,
        confirmed_by="admin_dashboard"
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res


@router.post("/{id}/reject", dependencies=[Depends(verify_admin_key)])
async def reject_payment(id: int, session: AsyncSession = Depends(get_db_session)):
    res = await payment_service.reject_payment(
        session=session,
        transaction_id=id,
        rejected_by="admin_dashboard"
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res
