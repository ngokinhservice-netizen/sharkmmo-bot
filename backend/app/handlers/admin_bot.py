import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, Order, PaymentTransaction, ProductCache, utcnow
from backend.app.services.canboso import canboso_client
from backend.app.services.product_sync import sync_canboso_products
from backend.app.payments.payment_service import payment_service
from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.admin_bot")
router = Router(name="admin_bot")


def is_admin(user: User) -> bool:
    return user.role == "admin" or user.telegram_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def handle_admin_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền truy cập bảng quản trị Admin.")
        return

    # Aggregate stats
    users_count = await session.scalar(select(func.count(User.id))) or 0
    orders_count = await session.scalar(select(func.count(Order.id))) or 0
    completed_orders = await session.scalar(select(func.count(Order.id)).where(Order.status == "completed")) or 0
    total_rev = await session.scalar(select(func.sum(Order.sell_price)).where(Order.status == "completed")) or 0.0
    total_profit = await session.scalar(select(func.sum(Order.profit)).where(Order.status == "completed")) or 0.0
    pending_deposits = await session.scalar(select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == "pending")) or 0

    text = (
        f"👑 <b>BẢNG ĐIỀU KHIỂN QUẢN TRỊ SHARKMMO</b>\n\n"
        f"👥 Tổng khách hàng: <b>{users_count}</b>\n"
        f"📦 Tổng đơn hàng: <b>{orders_count}</b> (Thành công: <b>{completed_orders}</b>)\n"
        f"💰 Tổng doanh thu: <b>{total_rev:,.0f} VND</b>\n"
        f"📈 Lợi nhuận gộp: <b>{total_profit:,.0f} VND</b>\n"
        f"⏳ Yêu cầu nạp chờ duyệt: <b>{pending_deposits}</b>\n\n"
        f"🛠️ <b>Lệnh nhanh dành cho Admin:</b>\n"
        f"• <code>/balance</code> : Kiểm tra số dư kho nguồn Canboso\n"
        f"• <code>/sync</code> : Đồng bộ lại sản phẩm từ Canboso\n"
        f"• <code>/stats</code> : Báo cáo thống kê chi tiết\n"
        f"• Web Admin Panel: <i>Truy cập Dashboard Next.js</i>"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("balance"))
async def handle_balance_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền quản trị.")
        return

    await message.answer("⏳ Đang truy vấn số dư nguồn từ Canboso API...")
    try:
        source_bal = await canboso_client.get_balance(force_refresh=True)
        bal_text = source_bal.balanceText or f"{source_bal.balance:,.0f} {source_bal.walletCurrency or 'VND'}"
        usdt_text = f"{source_bal.usdtBalance} USDT" if source_bal.usdtBalance else "0 USDT"

        # Customer wallet total
        total_cust_bal = await session.scalar(select(func.sum(User.balance))) or 0.0

        alert_msg = ""
        bal_vnd = source_bal.balanceVnd or source_bal.balance
        if bal_vnd < settings.SOURCE_BALANCE_ALERT_THRESHOLD:
            alert_msg = f"\n⚠️ <b>CẢNH BÁO:</b> Số dư nguồn Canboso đang thấp hơn {settings.SOURCE_BALANCE_ALERT_THRESHOLD:,.0f} VND. Vui lòng nạp thêm tiền vào kho Canboso!"

        text = (
            f"💼 <b>BÁO CÁO SỐ DƯ KHO NGUỒN & HỆ THỐNG</b>\n\n"
            f"🏦 <b>Số dư Canboso API:</b>\n"
            f"• Số dư: <b>{bal_text}</b>\n"
            f"• USDT: <b>{usdt_text}</b>\n"
            f"• Cập nhật: {source_bal.updatedAt or 'Vừa xong'}"
            f"{alert_msg}\n\n"
            f"👥 <b>Số dư ví khách hàng (SHARKMMO):</b>\n"
            f"• Tổng số dư ví thành viên: <b>{total_cust_bal:,.0f} VND</b>\n"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Lỗi truy vấn Canboso balance: {str(e)}")


@router.message(Command("sync"))
async def handle_sync_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền quản trị.")
        return

    await message.answer("⏳ Đang đồng bộ danh mục và sản phẩm từ Canboso API...")
    try:
        result = await sync_canboso_products(session, force_refresh=True)
        await message.answer(
            f"✅ <b>ĐỒNG BỘ HOÀN TẤT!</b>\n\n"
            f"• Tổng sản phẩm nguồn: <b>{result.get('total')}</b>\n"
            f"• Thêm mới: <b>{result.get('added')}</b>\n"
            f"• Cập nhật giá & kho: <b>{result.get('updated')}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Đồng bộ thất bại: {str(e)}")


@router.callback_query(F.data.startswith("adm_approve_dep:"))
async def handle_admin_approve_deposit(callback: CallbackQuery, session: AsyncSession, current_user: User):
    if not is_admin(current_user):
        await callback.answer("Bạn không có quyền admin.", show_alert=True)
        return

    tx_id = int(callback.data.split("adm_approve_dep:", 1)[1])
    res = await payment_service.confirm_payment(
        session=session,
        transaction_id=tx_id,
        confirmed_by=f"admin_{current_user.telegram_id}"
    )

    if res.get("success"):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"✅ Đã duyệt nạp tiền: <b>{res.get('transaction_code')}</b> (+{res.get('amount', 0):,.0f} VND) cho khách <code>{res.get('telegram_id')}</code>.",
            parse_mode="HTML"
        )
        await callback.answer("Duyệt thành công!")
    else:
        await callback.answer(f"Lỗi: {res.get('message')}", show_alert=True)


@router.callback_query(F.data.startswith("adm_reject_dep:"))
async def handle_admin_reject_deposit(callback: CallbackQuery, session: AsyncSession, current_user: User):
    if not is_admin(current_user):
        await callback.answer("Bạn không có quyền admin.", show_alert=True)
        return

    tx_id = int(callback.data.split("adm_reject_dep:", 1)[1])
    res = await payment_service.reject_payment(
        session=session,
        transaction_id=tx_id,
        rejected_by=f"admin_{current_user.telegram_id}"
    )

    if res.get("success"):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"❌ Đã từ chối giao dịch #{tx_id}.", parse_mode="HTML")
        await callback.answer("Đã từ chối giao dịch.")
    else:
        await callback.answer(f"Lỗi: {res.get('message')}", show_alert=True)
