from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, PaymentTransaction
from backend.app.payments.payment_service import payment_service
from backend.app.keyboards.menus import (
    get_deposit_amounts_keyboard,
    get_deposit_action_keyboard
)

router = Router(name="wallet")


class DepositState(StatesGroup):
    waiting_for_custom_amount = State()


@router.message(F.text == "💰 Ví của tôi")
async def show_wallet(message: Message, current_user: User, session: AsyncSession):
    # Fetch recent deposit transactions
    q = (
        select(PaymentTransaction)
        .where(PaymentTransaction.telegram_id == current_user.telegram_id)
        .order_by(PaymentTransaction.id.desc())
        .limit(5)
    )
    res = await session.execute(q)
    recent_txs = res.scalars().all()

    tx_history_text = ""
    if recent_txs:
        lines = []
        for tx in recent_txs:
            st_icon = "🟢 Thành công" if tx.status == "completed" else ("⏳ Chờ xử lý" if tx.status == "pending" else "🔴 Thất bại")
            lines.append(f"• {tx.transaction_code}: {tx.amount:,.0f}đ — {st_icon}")
        tx_history_text = "\n\n📋 <b>Lịch sử nạp gần đây:</b>\n" + "\n".join(lines)

    text = (
        f"💳 <b>VÍ ĐIỆN TỬ SHARKMMO</b>\n\n"
        f"👤 Chủ tài khoản: <b>{message.from_user.full_name}</b>\n"
        f"🆔 Telegram ID: <code>{current_user.telegram_id}</code>\n"
        f"💰 Số dư khả dụng: <b>{current_user.balance:,.0f} VND</b>\n"
        f"💸 Tổng đã chi tiêu: <b>{current_user.total_spent:,.0f} VND</b>\n"
        f"📦 Đơn hàng đã mua: <b>{current_user.total_orders} đơn</b>"
        f"{tx_history_text}\n\n"
        f"⚡ <i>Chọn mệnh giá nạp tiền bên dưới để tạo mã QR chuyển khoản tự động:</i>"
    )

    await message.answer(
        text=text,
        reply_markup=get_deposit_amounts_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("dep_amt:"))
async def handle_select_deposit_amount(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    amt_param = callback.data.split("dep_amt:", 1)[1]

    if amt_param == "custom":
        await state.set_state(DepositState.waiting_for_custom_amount)
        await callback.message.answer(
            "✏️ <b>Vui lòng nhập số tiền bạn muốn nạp (VND):</b>\n<i>Tối thiểu: 10,000 VND (Ví dụ: 150000)</i>",
            parse_mode="HTML"
        )
        await callback.answer()
        return

    amount = float(amt_param)
    await generate_and_send_qr(callback.message, session, current_user.telegram_id, amount)
    await callback.answer()


@router.message(DepositState.waiting_for_custom_amount)
async def handle_custom_deposit_input(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    text = message.text.strip().replace(".", "").replace(",", "").replace("k", "000").replace("K", "000")
    if not text.isdigit():
        await message.answer("⚠️ Số tiền không hợp lệ. Vui lòng nhập số nguyên (Ví dụ: 100000).")
        return

    amount = float(text)
    if amount < 10000:
        await message.answer("⚠️ Số tiền nạp tối thiểu là 10,000 VND. Vui lòng nhập lại:")
        return

    await state.clear()
    await generate_and_send_qr(message, session, current_user.telegram_id, amount)


async def generate_and_send_qr(
    target_msg: Message,
    session: AsyncSession,
    telegram_id: int,
    amount: float
):
    dep_res = await payment_service.create_deposit_request(
        session=session,
        telegram_id=telegram_id,
        amount=amount
    )

    if not dep_res.get("success"):
        await target_msg.answer(f"❌ {dep_res.get('message', 'Không thể tạo yêu cầu nạp tiền.')}")
        return

    tx_code = dep_res["transaction_code"]
    content = dep_res["transfer_content"]
    qr_url = dep_res["qr_url"]
    bank_code = dep_res["bank_code"]
    acc_no = dep_res["account_number"]
    acc_name = dep_res["account_name"]

    caption = (
        f"🏦 <b>THÔNG TIN CHUYỂN KHOẢN NẠP TIỀN</b>\n\n"
        f"💳 Ngân hàng: <b>{bank_code}</b>\n"
        f"🔢 Số tài khoản: <code>{acc_no}</code>\n"
        f"👤 Chủ tài khoản: <b>{acc_name}</b>\n"
        f"💰 Số tiền: <b>{amount:,.0f} VND</b>\n"
        f"📝 Nội dung CK: <code>{content}</code>\n\n"
        f"⚠️ <b>LƯU Ý QUAN TRỌNG:</b>\n"
        f"1. Quét mã QR hoặc sao chép <b>CHÍNH XÁC nội dung chuyển khoản</b> để hệ thống cộng tiền tự động trong 10-30 giây.\n"
        f"2. Mã giao dịch: <code>{tx_code}</code>"
    )

    await target_msg.answer_photo(
        photo=qr_url,
        caption=caption,
        reply_markup=get_deposit_action_keyboard(dep_res["transaction_id"]),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("check_dep:"))
async def check_deposit_status(callback: CallbackQuery, session: AsyncSession):
    tx_id = int(callback.data.split("check_dep:", 1)[1])
    q = select(PaymentTransaction).where(PaymentTransaction.id == tx_id)
    res = await session.execute(q)
    tx = res.scalars().first()

    if not tx:
        await callback.answer("Không tìm thấy giao dịch.", show_alert=True)
        return

    if tx.status == "completed":
        await callback.message.edit_caption(
            caption=(
                f"✅ <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n"
                f"Mã giao dịch: <code>{tx.transaction_code}</code>\n"
                f"Số tiền: <b>+{tx.amount:,.0f} VND</b> đã được cộng vào số dư ví của bạn.\n"
                f"Cảm ơn bạn đã tin tưởng sử dụng dịch vụ của SHARKMMO!"
            ),
            parse_mode="HTML"
        )
        await callback.answer("✅ Nạp tiền thành công!", show_alert=True)
    elif tx.status == "rejected":
        await callback.answer("❌ Giao dịch đã bị từ chối hoặc hết hạn.", show_alert=True)
    else:
        await callback.answer(
            "⏳ Hệ thống chưa nhận được thanh toán từ ngân hàng. Nếu bạn đã chuyển khoản, vui lòng chờ 15-30 giây để webhook xử lý hoặc gửi hóa đơn cho Admin.",
            show_alert=True
        )


@router.callback_query(F.data == "cancel_dep")
async def cancel_deposit(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer("Đã đóng giao dịch nạp tiền.")
