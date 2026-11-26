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
        Notifies Admin on Telegram for ALL incoming deposits,
        prevents duplicate webhook processing, and credits user if matching memo found.
        """
        gateway_id = str(payload.get("id") or "")
        raw_amount = (
            payload.get("transferAmount")
            or payload.get("amountIn")
            or payload.get("amount_in")
            or payload.get("amount")
            or payload.get("transfer_amount")
            or 0.0
        )
        amount_in = float(raw_amount)
        content = (
            payload.get("content")
            or payload.get("transactionContent")
            or payload.get("description")
            or ""
        ).strip()
        account_number = payload.get("accountNumber", "")
        tx_date = payload.get("transactionDate") or utcnow().strftime("%H:%M:%S %d/%m/%Y")

        logger.info(f"Incoming SePay webhook: ID={gateway_id}, Amount={amount_in}, Content='{content}'")

        if amount_in <= 0:
            return {"success": False, "message": "Ignored outgoing or zero-amount transaction."}

        # 1. Send instant Telegram alert to Admin for EVERY incoming deposit
        admin_chat_id = settings.ADMIN_IDS[0] if settings.ADMIN_IDS else 8650996593
        if settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("dummy"):
            try:
                from backend.app.bot.bot import create_bot
                bot = create_bot()
                async with bot:
                    admin_msg = (
                        "💰 <b>[SEPAY] THÔNG BÁO TIỀN VÀO TÀI KHOẢN!</b>\n"
                        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
                        f"💵 <b>Số tiền nạp:</b> <code>+{amount_in:,.0f} VND</code>\n"
                        f"📝 <b>Nội dung chuyển khoản:</b> <code>{content}</code>\n"
                        f"🏦 <b>Tài khoản nhận:</b> <code>{account_number}</code>\n"
                        f"🆔 <b>Mã SePay:</b> <code>{gateway_id or 'SePay-Auto'}</code>\n"
                        f"⏰ <b>Thời gian:</b> <code>{tx_date}</code>\n\n"
                        "⚡ <i>Hệ thống SePay tự động ghi nhận giao dịch!</i>"
                    )
                    await bot.send_message(chat_id=admin_chat_id, text=admin_msg, parse_mode="HTML")
            except Exception as e_notify:
                logger.error(f"Failed to send SePay admin notification: {e_notify}")

        # 2. Check idempotency: Have we already processed this gateway_tx_id?
        if gateway_id:
            duplicate_q = select(PaymentTransaction).where(PaymentTransaction.gateway_tx_id == gateway_id)
            dup_res = await session.execute(duplicate_q)
            existing_tx = dup_res.scalars().first()
            if existing_tx:
                logger.info(f"Webhook already processed for gateway_tx_id={gateway_id}")
                return {"success": True, "already_processed": True, "transaction_code": existing_tx.transaction_code}

        # 3. Match pending transaction by transfer content
        pending_q = select(PaymentTransaction).where(PaymentTransaction.status == "pending")
        res = await session.execute(pending_q)
        pending_txs = res.scalars().all()

        matched_tx: Optional[PaymentTransaction] = None
        for tx in pending_txs:
            clean_bank_content = re.sub(r"\s+", "", content.upper())
            clean_tx_content = re.sub(r"\s+", "", tx.transfer_content.upper())

            if clean_tx_content in clean_bank_content or tx.transfer_content.upper() in content.upper():
                if abs(tx.amount - amount_in) < 1.0:
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

        # 4. Fallback match: "SHARK NAP <TELEGRAM_ID>"
        match = re.search(r"SHARK\s*NAP\s*(\d{6,15})", content, re.IGNORECASE)
        if match:
            telegram_id = int(match.group(1))
            user_q = select(User).where(User.telegram_id == telegram_id)
            user_res = await session.execute(user_q)
            user = user_res.scalars().first()

            if user:
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

                # Notify user if matched
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
                                "⚡ <i>Cảm ơn bạn đã nạp tiền qua SePay!</i>"
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

        logger.info(f"General deposit received: Content='{content}', Amount={amount_in}")
        return {
            "success": True,
            "message": "Deposit recorded and admin notified successfully.",
            "amount": amount_in,
            "content": content
        }


sepay_processor = SePayProcessor()
