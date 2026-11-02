import asyncio
import datetime
import logging
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, ProductCache, Order, utcnow
from backend.app.services.canboso import (
    canboso_client,
    CanbosoAPIError,
    CanbosoRateLimitError,
    PurchaseResponse
)
from backend.app.services.pricing import pricing_engine

logger = logging.getLogger("sharkmmo.orders")

# In-memory user purchase locks to prevent double-click race conditions
_user_locks: Dict[int, asyncio.Lock] = {}


def get_user_lock(telegram_id: int) -> asyncio.Lock:
    if telegram_id not in _user_locks:
        _user_locks[telegram_id] = asyncio.Lock()
    return _user_locks[telegram_id]


class OrderService:
    @staticmethod
    def generate_order_code() -> str:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"SHARK-{date_str}-{random_suffix}"

    @classmethod
    async def create_purchase_order(
        cls,
        session: AsyncSession,
        telegram_id: int,
        product_id: str,
        quantity: int = 1,
        customer_email: Optional[str] = None,
        customer_accounts: Optional[List[str]] = None,
        slot_months: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes a secure automated purchase:
        1. Checks user lock & balance
        2. Verifies Canboso source balance & availability
        3. Calls Canboso purchase API with Idempotency-Key
        4. Saves delivery info & records profit
        5. Handles rollback on failure
        """
        lock = get_user_lock(telegram_id)
        async with lock:
            # 1. Fetch user
            user_query = select(User).where(User.telegram_id == telegram_id)
            user_res = await session.execute(user_query)
            user = user_res.scalars().first()

            if not user:
                return {"success": False, "message": "Không tìm thấy thông tin tài khoản người dùng."}

            if user.is_banned:
                return {"success": False, "message": "Tài khoản của bạn đã bị tạm khóa. Vui lòng liên hệ hỗ trợ."}

            # 2. Fetch product cache
            prod_query = select(ProductCache).where(ProductCache.product_id == product_id, ProductCache.is_active == True)
            prod_res = await session.execute(prod_query)
            product = prod_res.scalars().first()

            if not product:
                return {"success": False, "message": "Sản phẩm không tồn tại hoặc đã ngừng kinh doanh."}

            # Recalculate price strictly to prevent stale client tampering
            calc_unit_price, _ = await pricing_engine.calculate_product_price(session, product)
            total_sell_price = calc_unit_price * quantity
            total_source_price = product.source_price * quantity

            # 3. Check customer balance
            if user.balance < total_sell_price:
                missing = total_sell_price - user.balance
                return {
                    "success": False,
                    "need_deposit": True,
                    "message": f"Số dư không đủ! Cần {total_sell_price:,.0f}đ, hiện có {user.balance:,.0f}đ (thiếu {missing:,.0f}đ). Vui lòng nạp thêm tiền vào ví.",
                    "user_balance": user.balance,
                    "total_price": total_sell_price,
                    "missing_amount": missing
                }

            # 4. Check Canboso source wallet balance
            try:
                source_balance = await canboso_client.get_balance()
                source_wallet_vnd = source_balance.balanceVnd or source_balance.balance
                if source_wallet_vnd < total_source_price:
                    logger.critical(
                        f"ALERT: Canboso source balance is low ({source_wallet_vnd} VND) to fulfill order requiring {total_source_price} VND."
                    )
                    return {
                        "success": False,
                        "message": "Kho nguồn đang trong chu kỳ bảo trì/nạp thêm kho. Đơn hàng chưa bị trừ tiền, vui lòng thử lại sau ít phút hoặc báo Admin!"
                    }
            except Exception as e:
                logger.warning(f"Could not verify source balance, proceeding with caution: {e}")

            # 5. Create Order record in database with PROCESSING status
            order_code = cls.generate_order_code()
            idempotency_key = f"purchase-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:16]}"

            order = Order(
                order_code=order_code,
                user_id=user.id,
                telegram_id=telegram_id,
                product_id=product.product_id,
                product_name=product.name,
                product_type=product.product_type,
                quantity=quantity,
                source_price=product.source_price,
                sell_price=total_sell_price,
                profit=total_sell_price - total_source_price,
                customer_email=customer_email,
                customer_accounts=customer_accounts,
                slot_months=slot_months,
                status="processing",
                idempotency_key=idempotency_key,
                created_at=utcnow()
            )

            # Deduct user balance tentatively
            user.balance -= total_sell_price
            user.total_spent += total_sell_price
            user.total_orders += 1

            session.add(order)
            await session.commit()
            await session.refresh(order)

            # 6. Call Canboso API Purchase
            try:
                purchase_res: PurchaseResponse = await canboso_client.purchase(
                    product_id=product_id,
                    quantity=quantity,
                    customer_email=customer_email,
                    customer_accounts=customer_accounts,
                    slot_months=slot_months,
                    idempotency_key=idempotency_key
                )

                # Update order with delivery accounts & Canboso order code
                order.status = "completed"
                order.completed_at = utcnow()
                order.canboso_order_code = purchase_res.order.orderCode
                
                # Extract delivery accounts if any
                delivery_list = []
                if purchase_res.delivery and purchase_res.delivery.accounts:
                    for acc in purchase_res.delivery.accounts:
                        delivery_list.append(acc.model_dump())
                order.delivery_data = delivery_list

                # Update actual source price & profit from response if available
                if purchase_res.payment and purchase_res.payment.amount:
                    actual_source = purchase_res.payment.amount
                    order.source_price = actual_source / (quantity or 1)
                    order.profit = total_sell_price - actual_source

                await session.commit()

                return {
                    "success": True,
                    "order_code": order.order_code,
                    "canboso_order_code": order.canboso_order_code,
                    "product_name": order.product_name,
                    "quantity": order.quantity,
                    "sell_price": order.sell_price,
                    "delivery_data": delivery_list,
                    "user_balance": user.balance
                }

            except (CanbosoAPIError, Exception) as err:
                logger.error(f"Purchase failed for order {order_code}: {err}")
                # Rollback user balance
                user.balance += total_sell_price
                user.total_spent -= total_sell_price
                user.total_orders -= 1

                order.status = "failed"
                order.error_message = str(err)
                await session.commit()

                return {
                    "success": False,
                    "order_code": order_code,
                    "message": f"Mua hàng thất bại từ nhà cung cấp: {str(err)}. Tiền đã được hoàn lại đầy đủ vào ví của bạn.",
                    "refunded": True,
                    "user_balance": user.balance
                }


order_service = OrderService()
