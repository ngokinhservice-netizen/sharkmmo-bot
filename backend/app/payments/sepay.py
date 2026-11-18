import re
import logging
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import PaymentTransaction, User, utcnow
from backend.app.core.config import settings
from backend.app.payments.payment_service import payment_service

logger = logging.getLogger("sharkmmo.sepay")


class SePayProcessor:
    @classmethod
    async def process_webhook(cls, session: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process bank transfer incoming webhook from SePay.
        Prevents duplicate webhook processing, verifies amount and transfer memo.
        """
        gateway_id = str(payload.get("id") or "")
        amount_in = float(payload.get("amountIn") or 0.0)
        content = (payload.get("transactionContent") or payload.get("description") or "").strip()
        account_number = payload.get("accountNumber", "")

        logger.info(f"Incoming SePay webhook: ID={gateway_id}, Amount={amount_in}, Content='{content}'")

        if amount_in <= 0:
            return {"success": False, "message": "Ignored outgoing or zero-amount transaction."}

        # 1. Check idempotency: Have we already processed this gateway_tx_id?
        if gateway_id:
            duplicate_q = select(PaymentTransaction).where(PaymentTransaction.gateway_tx_id == gateway_id)
            dup_res = await session.execute(duplicate_q)
            existing_tx = dup_res.scalars().first()
            if existing_tx:
                logger.info(f"Webhook already processed for gateway_tx_id={gateway_id}")
                return {"success": True, "already_processed": True, "transaction_code": existing_tx.transaction_code}

        # 2. Match pending transaction by transfer content
        # Check all pending transactions
        pending_q = select(PaymentTransaction).where(PaymentTransaction.status == "pending")
        res = await session.execute(pending_q)
        pending_txs = res.scalars().all()

        matched_tx: Optional[PaymentTransaction] = None
        for tx in pending_txs:
            # Check if tx.transfer_content is contained in the bank transaction content (case-insensitive)
            # Remove spaces for resilient matching: "SHARKNAP1336962312"
            clean_bank_content = re.sub(r"\s+", "", content.upper())
            clean_tx_content = re.sub(r"\s+", "", tx.transfer_content.upper())

            if clean_tx_content in clean_bank_content or tx.transfer_content.upper() in content.upper():
                # Verify amount
                if abs(tx.amount - amount_in) < 1.0:  # Matching amount
                    matched_tx = tx
                    break

        if matched_tx:
            confirm_res = await payment_service.confirm_payment(
                session=session,
                transaction_id=matched_tx.id,
                confirmed_by="sepay_webhook",
                gateway_tx_id=gateway_id,
                gateway_data=payload
            )
            return confirm_res

        # 3. If no pending transaction matches exactly, try fallback match: "SHARK NAP <TELEGRAM_ID>"
        match = re.search(r"SHARK\s*NAP\s*(\d{6,15})", content, re.IGNORECASE)
        if match:
            telegram_id = int(match.group(1))
            user_q = select(User).where(User.telegram_id == telegram_id)
            user_res = await session.execute(user_q)
            user = user_res.scalars().first()

            if user:
                # Auto create completed transaction
                tx_code = payment_service.generate_tx_code()
                auto_tx = PaymentTransaction(
                    transaction_code=tx_code,
                    user_id=user.id,
                    telegram_id=user.telegram_id,
                    amount=amount_in,
                    payment_method="sepay_auto",
                    bank_code=settings.BANK_CODE,
                    account_number=account_number,
                    transfer_content=content[:100],
                    status="completed",
                    gateway_tx_id=gateway_id,
                    gateway_data=payload,
                    confirmed_by="sepay_auto_matched",
                    created_at=utcnow(),
                    confirmed_at=utcnow()
                )
                user.balance += amount_in
                session.add(auto_tx)
                await session.commit()
                logger.info(f"Auto-credited {amount_in} VND to user {telegram_id} based on memo match.")

                # Send Telegram notification
                if settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("dummy"):
                    try:
                        from backend.app.bot.bot import create_bot
                        bot = create_bot()
                        async with bot:
                            msg = (
                                "🎉 <b>NẠP TIỀN THÀNH CÔNG!</b>\n"
                                "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
                                f"🆔 Mã giao dịch: <code>{tx_code}</code>\n"
                                f"💰 Số tiền: <b>+{amount_in:,.0f} VND</b>\n"
                                f"💳 Số dư ví hiện có: <b>{user.balance:,.0f} VND</b>\n\n"
                                "⚡ <i>Hệ thống tự động cộng tiền qua SePay thành công!</i>\n"
                                "Bấm <b>🛍️ Mua sản phẩm</b> để bắt đầu mua sắm ngay!"
                            )
                            await bot.send_message(chat_id=user.telegram_id, text=msg, parse_mode="HTML")
                    except Exception as e_notify:
                        logger.error(f"Failed to send deposit confirmation notification: {e_notify}")

                return {
                    "success": True,
                    "auto_credited": True,
                    "telegram_id": telegram_id,
                    "amount": amount_in,
                    "new_balance": user.balance
                }

        logger.warning(f"Unmatched payment transaction: Content='{content}', Amount={amount_in}")
        return {"success": False, "message": "No matching pending transaction or valid user ID found in content."}


sepay_processor = SePayProcessor()
