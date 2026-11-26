import random
import logging
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, PaymentTransaction, utcnow
from backend.app.keyboards.menus import (
    get_main_menu,
    get_qr_amount_keyboard,
    get_qr_action_keyboard,
)
from backend.app.payments.vietqr import get_vietqr_url
from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.start")
router = Router(name="start")

BANK_CODE = "VPB"
BANK_NAME = "VPBank"
ACCOUNT_NO = "0342938622"
ACCOUNT_NAME = "LE DANG KHOA"


class QrForm(StatesGroup):
    waiting_for_amount = State()


# 1. Main /start command
@router.message(CommandStart())
@router.message(Command("menu"))
@router.message(Command("help"))
async def handle_start(message: Message, current_user: User):
    first_name = message.from_user.first_name or "Sếp"
    text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "      🔥 <b>SHARK PAYMENT & STATS BOT</b> 🔥\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"👋 Xin chào <b>{first_name}</b>!\n"
        f"🆔 ID Telegram: <code>{message.from_user.id}</code>\n"
        f"🏦 Tài khoản nhận: <b>{BANK_NAME} - <code>{ACCOUNT_NO}</code></b>\n"
        f"👤 Chủ tài khoản: <b>{ACCOUNT_NAME}</b>\n\n"
        "⚡ <i>Hệ thống tự động theo dõi tiền vào qua SePay và tạo mã VietQR động!</i>\n\n"
        "👇 <b>Bấm chọn chức năng bên dưới bàn phím:</b>"
    )
    await message.answer(text=text, reply_markup=get_main_menu(), parse_mode="HTML")


# 2. View Monthly Revenue Button
@router.message(F.text == "📊 Doanh Thu Tháng Này")
@router.message(Command("doanhthu"))
async def handle_revenue_month(message: Message, session: AsyncSession, current_user: User):
    now = utcnow()
    start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    start_of_today = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    # 1. Monthly revenue
    q_month = select(
        func.coalesce(func.sum(PaymentTransaction.amount), 0.0),
        func.count(PaymentTransaction.id),
    ).where(
        PaymentTransaction.status == "completed",
        PaymentTransaction.created_at >= start_of_month,
    )
    res_month = await session.execute(q_month)
    total_month, count_month = res_month.first()

    # 2. Today revenue
    q_today = select(
        func.coalesce(func.sum(PaymentTransaction.amount), 0.0),
        func.count(PaymentTransaction.id),
    ).where(
        PaymentTransaction.status == "completed",
        PaymentTransaction.created_at >= start_of_today,
    )
    res_today = await session.execute(q_today)
    total_today, count_today = res_today.first()

    text = (
        f"📊 <b>BÁO CÁO THU NHẬP THÁNG {now.month}/{now.year}</b>\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"🏦 <b>Ngân hàng:</b> {BANK_NAME}\n"
        f"💳 <b>Số tài khoản:</b> <code>{ACCOUNT_NO}</code>\n"
        f"👤 <b>Chủ tài khoản:</b> <code>{ACCOUNT_NAME}</code>\n\n"
        f"💰 <b>Tổng tiền nhận tháng {now.month}:</b> <code>+{total_month:,.0f} VND</code>\n"
        f"📈 <b>Tổng số giao dịch thành công:</b> <b>{count_month}</b> giao dịch\n\n"
        f"📅 <b>Hôm nay đã nhận:</b> <code>+{total_today:,.0f} VND</code> ({count_today} giao dịch)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <i>Dữ liệu được thống kê tự động từ biến động số dư SePay!</i>"
    )
    await message.answer(text=text, parse_mode="HTML")


# 3. View Bank Account Info Button
@router.message(F.text == "🏦 Thông Tin Tài Khoản VPBank")
async def handle_bank_info(message: Message):
    text = (
        "🏦 <b>THÔNG TIN TÀI KHOẢN NHẬN TIỀN</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>Ngân hàng:</b> {BANK_NAME} (Việt Nam Thịnh Vượng)\n"
        f"• <b>Số tài khoản:</b> <code>{ACCOUNT_NO}</code> (Bấm để copy)\n"
        f"• <b>Chủ tài khoản:</b> <code>{ACCOUNT_NAME}</code>\n"
        "• <b>Trạng thái cổng SePay:</b> 🟢 Đang hoạt động (Auto 24/7)\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(text=text, parse_mode="HTML")


# 4. Trigger Create QR Code
@router.message(F.text == "⚡ Tạo Mã QR Thanh Toán")
@router.message(Command("qr"))
async def handle_create_qr_prompt(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "⚡ <b>TẠO MÃ QR THANH TOÁN TỰ ĐỘNG</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏦 <b>Tài khoản nhận:</b> {BANK_NAME} - <code>{ACCOUNT_NO}</code>\n"
        f"👤 <b>Chủ TK:</b> <code>{ACCOUNT_NAME}</code>\n\n"
        "👇 <b>Chọn số tiền bạn muốn tạo mã QR hoặc nhập số tùy ý:</b>"
    )
    await message.answer(text=text, reply_markup=get_qr_amount_keyboard(), parse_mode="HTML")


# 5. Handle Preset Amount Selection
@router.callback_query(F.data.startswith("qr_amt:"))
async def handle_qr_preset(
    callback: CallbackQuery, session: AsyncSession, current_user: User, state: FSMContext
):
    action = callback.data.split(":")[1]

    if action == "custom":
        await state.set_state(QrForm.waiting_for_amount)
        await callback.message.edit_text(
            "✏️ <b>Vui lòng nhập số tiền bạn muốn tạo mã QR</b>\n"
            "<i>(Ví dụ: 150000 hoặc 350000):</i>",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    try:
        amount = float(action)
        await callback.answer("Đang tạo mã QR VietQR...")
        await generate_and_send_qr(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            user=current_user,
            session=session,
            amount=amount,
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error creating preset QR: {e}")
        await callback.answer("Lỗi khi tạo mã QR!", show_alert=True)


# 6. Handle Custom Amount Text Input
@router.message(QrForm.waiting_for_amount)
async def handle_custom_amount_text(
    message: Message, session: AsyncSession, current_user: User, state: FSMContext
):
    raw_text = (message.text or "").replace(".", "").replace(",", "").replace("k", "000").replace("K", "000").strip()

    if not raw_text.isdigit():
        await message.answer(
            "❌ Số tiền không hợp lệ! Vui lòng nhập số tiền bằng số (Ví dụ: <code>150000</code>):",
            parse_mode="HTML",
        )
        return

    amount = float(raw_text)
    if amount < 1000:
        await message.answer("❌ Số tiền tối thiểu là 1,000 VND. Vui lòng nhập lại:")
        return

    if amount > 500_000_000:
        await message.answer("❌ Số tiền tối đa là 500,000,000 VND. Vui lòng nhập lại:")
        return

    await state.clear()
    await generate_and_send_qr(
        bot=message.bot,
        chat_id=message.chat.id,
        user=current_user,
        session=session,
        amount=amount,
    )


# 7. Helper: Generate and send VietQR photo
async def generate_and_send_qr(bot, chat_id: int, user: User, session: AsyncSession, amount: float):
    # Generate unique random transfer content memo (e.g. SHARK849201)
    memo = ""
    for _ in range(10):
        test_memo = f"SHARK{random.randint(100000, 999999)}"
        exists = await session.scalar(
            select(PaymentTransaction.id).where(PaymentTransaction.transfer_content == test_memo)
        )
        if not exists:
            memo = test_memo
            break

    if not memo:
        memo = f"SHARK{int(datetime.now().timestamp()) % 1000000:06d}"

    # Generate VietQR Image URL
    qr_url = get_vietqr_url(
        amount=amount,
        transfer_content=memo,
        bank_code=BANK_CODE,
        account_no=ACCOUNT_NO,
        account_name=ACCOUNT_NAME,
        template="compact2",
    )

    # Create Pending Payment Transaction in Database
    tx = PaymentTransaction(
        transaction_code=memo,
        user_id=user.id,
        telegram_id=user.telegram_id,
        amount=amount,
        payment_method="vietqr",
        bank_code=BANK_CODE,
        account_number=ACCOUNT_NO,
        transfer_content=memo,
        status="pending",
        created_at=utcnow(),
    )
    session.add(tx)
    await session.commit()
    await session.refresh(tx)

    caption = (
        "⚡ <b>MÃ QR THANH TOÁN TỰ ĐỘNG</b>\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"🏦 <b>Ngân hàng:</b> {BANK_NAME} (Việt Nam Thịnh Vượng)\n"
        f"💳 <b>Số tài khoản:</b> <code>{ACCOUNT_NO}</code>\n"
        f"👤 <b>Chủ tài khoản:</b> <code>{ACCOUNT_NAME}</code>\n"
        f"💰 <b>Số tiền:</b> <code>+{amount:,.0f} VND</code>\n"
        f"📝 <b>Nội dung chuyển khoản:</b> <code>{memo}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👉 <b>Bấm vào số tài khoản hoặc nội dung để tự động copy!</b>\n"
        "⚡ <i>Sau khi quét mã thanh toán, mã QR này sẽ tự động biến mất và bot sẽ lập tức thông báo tiền về!</i>"
    )

    action_kb = get_qr_action_keyboard(tx_id=tx.id, memo=memo, qr_url=qr_url)

    # Send QR Photo
    photo_msg = await bot.send_photo(
        chat_id=chat_id,
        photo=qr_url,
        caption=caption,
        reply_markup=action_kb,
        parse_mode="HTML",
    )

    # Save chat_id and message_id so SePay webhook can auto-delete the QR!
    tx.gateway_data = {"chat_id": chat_id, "message_id": photo_msg.message_id}
    await session.commit()


# 8. Handle Copy Information Callback
@router.callback_query(F.data.startswith("qr_copy:"))
async def handle_copy_info(callback: CallbackQuery):
    memo = callback.data.split(":")[1]
    copy_text = (
        f"STK: {ACCOUNT_NO}\n"
        f"Ngân hàng: {BANK_NAME}\n"
        f"Chủ TK: {ACCOUNT_NAME}\n"
        f"Nội dung: {memo}"
    )
    await callback.answer("Đã tạo mẫu sao chép!", show_alert=False)
    await callback.message.reply(
        f"📋 <b>Sao chép nhanh thông tin chuyển khoản:</b>\n\n"
        f"<code>{copy_text}</code>\n\n"
        f"<i>(Chạm vào đoạn văn bản trên để copy toàn bộ)</i>",
        parse_mode="HTML",
    )


# 9. Handle Cancel QR
@router.callback_query(F.data.startswith("qr_cancel_tx:"))
async def handle_cancel_tx(callback: CallbackQuery, session: AsyncSession):
    tx_id = int(callback.data.split(":")[1])
    tx = await session.get(PaymentTransaction, tx_id)
    if tx and tx.status == "pending":
        tx.status = "expired"
        await session.commit()

    try:
        await callback.message.delete()
        await callback.message.answer("❌ <b>Đã hủy mã QR thanh toán.</b>", parse_mode="HTML")
    except Exception:
        await callback.message.edit_caption(
            caption="❌ <b>MÃ QR ĐÃ ĐƯỢC HỦY.</b>",
            parse_mode="HTML",
        )
    await callback.answer("Đã hủy mã QR!")


# 10. Handle Cancel button from prompt
@router.callback_query(F.data == "qr_cancel")
async def handle_cancel_prompt(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Đã hủy.")
