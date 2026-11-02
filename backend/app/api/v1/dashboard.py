import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import User, Order, PaymentTransaction, ProductCache
from backend.app.services.canboso import canboso_client

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", dependencies=[Depends(verify_admin_key)])
async def get_dashboard_stats(session: AsyncSession = Depends(get_db_session)):
    # Counts
    total_users = await session.scalar(select(func.count(User.id))) or 0
    total_orders = await session.scalar(select(func.count(Order.id))) or 0
    completed_orders = await session.scalar(select(func.count(Order.id)).where(Order.status == "completed")) or 0
    failed_orders = await session.scalar(select(func.count(Order.id)).where(Order.status == "failed")) or 0
    processing_orders = await session.scalar(select(func.count(Order.id)).where(Order.status == "processing")) or 0

    # Revenue & Gross Profit
    total_revenue = await session.scalar(select(func.sum(Order.sell_price)).where(Order.status == "completed")) or 0.0
    total_profit = await session.scalar(select(func.sum(Order.profit)).where(Order.status == "completed")) or 0.0
    total_customer_balance = await session.scalar(select(func.sum(User.balance))) or 0.0

    # Pending Deposits
    pending_deposits = await session.scalar(select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == "pending")) or 0

    # Canboso Source Balance
    source_balance_info = {
        "balance": 0.0,
        "currency": "VND",
        "formatted": "0 VND",
        "usdt": 0.0,
        "is_low": False,
        "status": "connected"
    }

    try:
        canboso_bal = await canboso_client.get_balance()
        b_vnd = canboso_bal.balanceVnd or canboso_bal.balance
        source_balance_info = {
            "balance": b_vnd,
            "currency": canboso_bal.walletCurrency or "VND",
            "formatted": canboso_bal.balanceText or f"{b_vnd:,.0f} VND",
            "usdt": canboso_bal.usdtBalance or 0.0,
            "is_low": b_vnd < 100000.0,
            "status": "connected"
        }
    except Exception as e:
        source_balance_info["status"] = f"error: {str(e)}"

    # Chart data for the last 7 days
    now = datetime.datetime.now(datetime.timezone.utc)
    chart_data = []
    for i in range(6, -1, -1):
        day_date = (now - datetime.timedelta(days=i)).date()
        day_start = datetime.datetime.combine(day_date, datetime.time.min, tzinfo=datetime.timezone.utc)
        day_end = datetime.datetime.combine(day_date, datetime.time.max, tzinfo=datetime.timezone.utc)

        rev_q = select(func.sum(Order.sell_price)).where(
            Order.status == "completed",
            Order.created_at >= day_start,
            Order.created_at <= day_end
        )
        day_rev = await session.scalar(rev_q) or 0.0

        profit_q = select(func.sum(Order.profit)).where(
            Order.status == "completed",
            Order.created_at >= day_start,
            Order.created_at <= day_end
        )
        day_profit = await session.scalar(profit_q) or 0.0

        chart_data.append({
            "date": day_date.strftime("%d/%m"),
            "revenue": round(day_rev, 2),
            "profit": round(day_profit, 2)
        })

    return {
        "success": True,
        "overview": {
            "total_users": total_users,
            "total_orders": total_orders,
            "completed_orders": completed_orders,
            "failed_orders": failed_orders,
            "processing_orders": processing_orders,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "total_customer_balance": total_customer_balance,
            "pending_deposits": pending_deposits,
            "source_balance": source_balance_info
        },
        "chart_data": chart_data
    }
