import datetime
import logging
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, PaymentTransaction, utcnow
from backend.app.core.config import settings
from backend.app.payments.vietqr import get_vietqr_url

logger = logging.getLogger("sharkmmo.payments")


class PaymentService:
    @staticmethod
    def generate_tx_code() -> str:
        date_str = datetime.datetime.now().strftime("%y%m%d")
        random_suffix = uuid.uuid4().hex[:6].upper()
        return f"NAP{date_str}{random_suffix}"

    @classmethod
    async def create_deposit_request(
        cls,
        session: AsyncSession,
        telegram_id: int,
        amount: float
    ) -> Dict[str, Any]:
        """
        Creates a pending deposit request and generates VietQR code
        """
        if amount < 10000:
            return {"success": False, "message": "Số tiền nạp tối thiểu là 10,000 VND."}

        # Check user
        user_res = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = user_res.scalars().first()
        if not user:
            return {"success": False, "message": "Người dùng không tồn tại."}

        tx_code = cls.generate_tx_code()
        # Transfer content format: SHARK NAP <TELEGRAM_ID> <TX_CODE_SUFFIX>
        transfer_content = f"SHARK NAP {telegram_id} {tx_code[-6:]}"

        tx = PaymentTransaction(
            transaction_code=tx_code,
            user_id=user.id,
            telegram_id=telegram_id,
            amount=amount,
            payment_method="vietqr",
            bank_code=settings.BANK_CODE,
            account_number=settings.BANK_ACCOUNT_NO,
            transfer_content=transfer_content,
            status="pending",
            created_at=utcnow()
        )

        session.add(tx)
        await session.commit()
        await session.refresh(tx)

        qr_url = get_vietqr_url(
            amount=amount,
            transfer_content=transfer_content,
            bank_code=settings.BANK_CODE,
            account_no=settings.BANK_ACCOUNT_NO,
            account_name=settings.BANK_ACCOUNT_NAME
        )

        return {
            "success": True,
            "transaction_id": tx.id,
            "transaction_code": tx.transaction_code,
            "amount": tx.amount,
            "bank_code": tx.bank_code,
            "account_number": tx.account_number,
            "account_name": settings.BANK_ACCOUNT_NAME,
            "transfer_content": tx.transfer_content,
            "qr_url": qr_url
        }

    @classmethod
    async def confirm_payment(
        cls,
        session: AsyncSession,
        transaction_id: int,
        confirmed_by: str = "system",
        gateway_tx_id: Optional[str] = None,
        gateway_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Confirms a payment transaction and adds balance to the user's wallet.
        Guarantees idempotency (will not double-credit).
        """
        tx_res = await session.execute(select(PaymentTransaction).where(PaymentTransaction.id == transaction_id))
        tx = tx_res.scalars().first()
        if not tx:
            return {"success": False, "message": "Không tìm thấy giao dịch."}

        if tx.status == "completed":
            return {"success": True, "already_completed": True, "message": "Giao dịch đã được duyệt trước đó."}

        if tx.status == "rejected":
            return {"success": False, "message": "Giao dịch đã bị từ chối trước đó."}

        user_res = await session.execute(select(User).where(User.id == tx.user_id))
        user = user_res.scalars().first()
        if not user:
            return {"success": False, "message": "Không tìm thấy người dùng."}

        # Credit balance
        user.balance += tx.amount
        tx.status = "completed"
        tx.confirmed_at = utcnow()
        tx.confirmed_by = confirmed_by
        if gateway_tx_id:
            tx.gateway_tx_id = str(gateway_tx_id)

        # Extract stored QR message metadata to auto-delete QR image
        qr_meta = tx.gateway_data if isinstance(tx.gateway_data, dict) else {}
        qr_chat_id = qr_meta.get("chat_id")
        qr_msg_id = qr_meta.get("message_id")

        if gateway_data:
            merged_meta = dict(qr_meta)
            merged_meta["sepay_payload"] = gateway_data
            tx.gateway_data = merged_meta

        await session.commit()
        logger.info(f"Payment confirmed: tx={tx.transaction_code}, amount={tx.amount}, user={user.telegram_id}, by={confirmed_by}")

        # Auto-delete QR code & send confirmation notification
        if settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("dummy"):
            try:
                from backend.app.bot.bot import create_bot
                bot = create_bot()
                async with bot:
                    # 1. DELETE QR MESSAGE SO IT DISAPPEARS IMMEDIATELY
                    if qr_chat_id and qr_msg_id:
                        try:
                            await bot.delete_message(chat_id=qr_chat_id, message_id=qr_msg_id)
                            logger.info(f"Successfully deleted QR message {qr_msg_id} in chat {qr_chat_id}")
                        except Exception as e_del:
                            logger.warning(f"Could not delete QR message {qr_msg_id}: {e_del}")
                            try:
                                await bot.edit_message_caption(
                                    chat_id=qr_chat_id,
                                    message_id=qr_msg_id,
                                    caption="✅ <b>GIAO DỊCH ĐÃ THANH TOÁN THÀNH CÔNG!</b>",
                                    parse_mode="HTML"
                                )
                            except Exception:
                                pass

                    # 2. SEND SUCCESS NOTIFICATION
                    time_str = utcnow().strftime("%H:%M:%S %d/%m/%Y")
                    msg = (
                        "🎉 <b>CỘNG TIỀN THÀNH CÔNG!</b>\n"
                        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
                        f"💰 <b>Số tiền nhận:</b> <code>+{tx.amount:,.0f} VND</code>\n"
                        f"📝 <b>Nội dung:</b> <code>{tx.transfer_content}</code>\n"
                        f"🏦 <b>Tài khoản nhận:</b> VPBank - <code>0342938622</code>\n"
                        f"👤 <b>Chủ tài khoản:</b> LE DANG KHOA\n"
                        f"🆔 <b>Mã SePay:</b> <code>{gateway_tx_id or tx.transaction_code}</code>\n"
                        f"⏰ <b>Thời gian:</b> <code>{time_str}</code>\n\n"
                        "⚡ <i>Hệ thống SePay tự động ghi nhận tiền vào tài khoản!</i>"
                    )

                    target_chat = qr_chat_id or user.telegram_id
                    await bot.send_message(chat_id=target_chat, text=msg, parse_mode="HTML")

                    admin_chat_id = settings.ADMIN_IDS[0] if settings.ADMIN_IDS else 8650996593
                    if str(target_chat) != str(admin_chat_id):
                        await bot.send_message(chat_id=admin_chat_id, text=msg, parse_mode="HTML")
            except Exception as e_notify:
                logger.error(f"Failed to send deposit confirmation notification: {e_notify}")

        return {
            "success": True,
            "transaction_code": tx.transaction_code,
            "telegram_id": user.telegram_id,
            "amount": tx.amount,
            "new_balance": user.balance
        }

    @classmethod
    async def reject_payment(
        cls,
        session: AsyncSession,
        transaction_id: int,
        rejected_by: str = "admin"
    ) -> Dict[str, Any]:
        tx_res = await session.execute(select(PaymentTransaction).where(PaymentTransaction.id == transaction_id))
        tx = tx_res.scalars().first()
        if not tx:
            return {"success": False, "message": "Không tìm thấy giao dịch."}

        if tx.status != "pending":
            return {"success": False, "message": f"Không thể từ chối giao dịch ở trạng thái '{tx.status}'."}

        tx.status = "rejected"
        tx.confirmed_by = rejected_by
        tx.confirmed_at = utcnow()
        await session.commit()

        return {"success": True, "message": "Đã từ chối giao dịch."}


payment_service = PaymentService()
