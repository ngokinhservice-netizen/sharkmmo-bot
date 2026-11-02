from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import Order, User, utcnow

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", dependencies=[Depends(verify_admin_key)])
async def list_orders(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(Order)
    if status:
        q = q.where(Order.status == status)
    if search:
        pat = f"%{search}%"
        q = q.where(or_(Order.order_code.ilike(pat), Order.product_name.ilike(pat)))

    q = q.order_by(Order.id.desc()).offset(offset).limit(limit)
    res = await session.execute(q)
    orders = res.scalars().all()

    items = []
    for o in orders:
        items.append({
            "id": o.id,
            "order_code": o.order_code,
            "telegram_id": o.telegram_id,
            "product_id": o.product_id,
            "product_name": o.product_name,
            "product_type": o.product_type,
            "quantity": o.quantity,
            "source_price": o.source_price,
            "sell_price": o.sell_price,
            "profit": o.profit,
            "status": o.status,
            "canboso_order_code": o.canboso_order_code,
            "delivery_data": o.delivery_data,
            "error_message": o.error_message,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "completed_at": o.completed_at.isoformat() if o.completed_at else None
        })

    return {"success": True, "count": len(items), "orders": items}


@router.get("/{id}", dependencies=[Depends(verify_admin_key)])
async def get_order_detail(id: int, session: AsyncSession = Depends(get_db_session)):
    q = select(Order).where(Order.id == id)
    res = await session.execute(q)
    order = res.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"success": True, "order": order}


@router.post("/{id}/refund", dependencies=[Depends(verify_admin_key)])
async def refund_order(id: int, session: AsyncSession = Depends(get_db_session)):
    q = select(Order).where(Order.id == id)
    res = await session.execute(q)
    order = res.scalars().first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "refunded":
        raise HTTPException(status_code=400, detail="Order already refunded")

    user_q = select(User).where(User.id == order.user_id)
    user_res = await session.execute(user_q)
    user = user_res.scalars().first()

    if user:
        user.balance += order.sell_price
        user.total_spent -= order.sell_price

    order.status = "refunded"
    order.profit = 0.0
    await session.commit()

    return {"success": True, "message": f"Order {order.order_code} refunded {order.sell_price} VND to user."}
