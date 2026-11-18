import logging
from typing import Optional, List
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, ProductCache
from backend.app.services.order_service import order_service
from backend.app.services.pricing import pricing_engine
from backend.app.keyboards.menus import (
    get_quantity_keyboard,
    get_slot_months_keyboard,
    get_confirm_purchase_keyboard
)

logger = logging.getLogger("sharkmmo.buy_flow")
router = Router(name="buy_flow")


class BuyState(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_slot_months = State()
    waiting_for_email = State()
    waiting_for_accounts = State()
    waiting_for_confirmation = State()


@router.callback_query(F.data.startswith("buy:"))
async def handle_start_buy(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    product_id = callback.data.split("buy:", 1)[1]
    q = select(ProductCache).where(ProductCache.product_id == product_id, ProductCache.is_active == True)
    res = await session.execute(q)
    product = res.scalars().first()

    if not product:
        await callback.answer("Sản phẩm không khả dụng hoặc đã bị ẩn.", show_alert=True)
        return

    # Check available stock
    if product.available_qty is not None and product.available_qty <= 0:
        await callback.answer("Sản phẩm hiện đang tạm hết hàng.", show_alert=True)
        return

    reqs = product.purchase_requirements or {}
    unit_price, _ = await pricing_engine.calculate_product_price(session, product)

    # Save initial purchase context to FSM
    await state.update_data(
        product_id=product.product_id,
        product_name=product.name,
        unit_price=unit_price,
        product_type=product.product_type,
        requirements=reqs,
        quantity=1,
        slot_months=None,
        customer_email=None,
        customer_accounts=[]
    )

    # Check if slot months required
    allowed_months = reqs.get("allowedMonths")
    if reqs.get("slotMonths") and allowed_months:
        await state.set_state(BuyState.waiting_for_slot_months)
        await callback.message.edit_text(
            f"🦈 <b>ĐẶT HÀNG: {product.name}</b>\n\n"
            f"Vui lòng chọn <b>thời hạn gói đăng ký</b> bạn muốn mua:",
            reply_markup=get_slot_months_keyboard(product.product_id, allowed_months),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Check if quantity is fixed
    if reqs.get("quantityFixed"):
        fixed_q = int(reqs["quantityFixed"])
        await state.update_data(quantity=fixed_q)
        await proceed_to_inputs_or_confirm(callback.message, state, session, current_user)
        await callback.answer()
        return

    # For slot products, quantity is typically 1
    if product.product_type == "slot":
        await state.update_data(quantity=1)
        await proceed_to_inputs_or_confirm(callback.message, state, session, current_user)
        await callback.answer()
        return

    # Otherwise ask for quantity
    await state.set_state(BuyState.waiting_for_quantity)
    await callback.message.edit_text(
        f"🦈 <b>ĐẶT HÀNG: {product.name}</b>\n"
        f"💰 Đơn giá: <b>{unit_price:,.0f} VND</b>\n\n"
        f"Vui lòng chọn hoặc nhập số lượng muốn mua:",
        reply_markup=get_quantity_keyboard(product.product_id),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(BuyState.waiting_for_slot_months, F.data.startswith("month:"))
async def handle_select_slot_month(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    parts = callback.data.split(":")
    months = int(parts[2])
    await state.update_data(slot_months=months)
    await proceed_to_inputs_or_confirm(callback.message, state, session, current_user)
    await callback.answer()


@router.callback_query(BuyState.waiting_for_quantity, F.data.startswith("qty:"))
async def handle_select_quantity_btn(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    parts = callback.data.split(":")
    qty = int(parts[2])
    await state.update_data(quantity=qty)
    await proceed_to_inputs_or_confirm(callback.message, state, session, current_user)
    await callback.answer()


@router.message(BuyState.waiting_for_quantity)
async def handle_manual_quantity_msg(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Số lượng không hợp lệ. Vui lòng nhập số nguyên dương (Ví dụ: 1, 2, 5).")
        return

    qty = int(text)
    if qty > 50:
        await message.answer("⚠️ Số lượng mỗi lần mua tối đa là 50 cái để đảm bảo an toàn giao dịch.")
        return

    await state.update_data(quantity=qty)
    await proceed_to_inputs_or_confirm(message, state, session, current_user)


async def proceed_to_inputs_or_confirm(
    target_msg: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    data = await state.get_data()
    reqs = data.get("requirements") or {}

    # Check if email is required
    if reqs.get("customerEmail") and not data.get("customer_email"):
        await state.set_state(BuyState.waiting_for_email)
        text = (
            f"📧 <b>YÊU CẦU EMAIL:</b>\n\n"
            f"Sản phẩm <b>{data['product_name']}</b> yêu cầu địa chỉ email để kích hoạt / nhận thông báo.\n"
            f"Vui lòng gửi địa chỉ email của bạn (Ví dụ: <code>example@gmail.com</code>):"
        )
        if hasattr(target_msg, "edit_text"):
            await target_msg.edit_text(text, parse_mode="HTML")
        else:
            await target_msg.answer(text, parse_mode="HTML")
        return

    # Check if customer accounts identifiers are required
    if reqs.get("customerAccounts") and not data.get("customer_accounts"):
        await state.set_state(BuyState.waiting_for_accounts)
        qty = data.get("quantity", 1)
        text = (
            f"📝 <b>YÊU CẦU ĐỊNH DANH TÀI KHOẢN:</b>\n\n"
            f"Bạn đang mua số lượng <b>{qty}</b> gói nâng cấp.\n"
            f"Vui lòng nhập chính xác <b>{qty}</b> tài khoản / email (mỗi dòng 1 tài khoản):"
        )
        if hasattr(target_msg, "edit_text"):
            await target_msg.edit_text(text, parse_mode="HTML")
        else:
            await target_msg.answer(text, parse_mode="HTML")
        return

    # All inputs ready, show confirmation
    await show_order_confirmation(target_msg, state, session, current_user)


@router.message(BuyState.waiting_for_email)
async def handle_input_email(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    email = message.text.strip()
    if "@" not in email or "." not in email or len(email) < 5:
        await message.answer("⚠️ Địa chỉ email không hợp lệ. Vui lòng nhập lại (Ví dụ: <code>buyer@gmail.com</code>):", parse_mode="HTML")
        return

    await state.update_data(customer_email=email)
    await proceed_to_inputs_or_confirm(message, state, session, current_user)


@router.message(BuyState.waiting_for_accounts)
async def handle_input_accounts(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    data = await state.get_data()
    qty = data.get("quantity", 1)
    lines = [line.strip() for line in message.text.split("\n") if line.strip()]

    if len(lines) != qty:
        await message.answer(
            f"⚠️ Bạn cần nhập đúng <b>{qty}</b> tài khoản (mỗi dòng 1 tài khoản). Bạn vừa nhập {len(lines)} dòng. Vui lòng nhập lại:",
            parse_mode="HTML"
        )
        return

    await state.update_data(customer_accounts=lines)
    await proceed_to_inputs_or_confirm(message, state, session, current_user)


async def show_order_confirmation(
    target_msg: Message,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    await state.set_state(BuyState.waiting_for_confirmation)
    data = await state.get_data()

    product_id = data["product_id"]
    product_name = data["product_name"]
    unit_price = data["unit_price"]
    quantity = data["quantity"]
    total_price = unit_price * quantity
    balance = current_user.balance

    extra_info = []
    if data.get("slot_months"):
        extra_info.append(f"• Thời hạn: <b>{data['slot_months']} tháng</b>")
    if data.get("customer_email"):
        extra_info.append(f"• Email kích hoạt: <code>{data['customer_email']}</code>")
    if data.get("customer_accounts"):
        extra_info.append(f"• DS tài khoản: <code>{', '.join(data['customer_accounts'])}</code>")

    extra_str = "\n".join(extra_info)
    if extra_str:
        extra_str = "\n" + extra_str

    if balance < total_price:
        missing = total_price - balance
        text = (
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
            "   ⚠️ <b>XÁC NHẬN ĐƠN — SỐ DƯ THIẾU</b> ⚠️\n"
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
            f"📦 <b>Sản phẩm:</b> <b>{product_name}</b>\n"
            f"🔢 <b>Số lượng:</b> <b>{quantity}</b>\n"
            f"💰 <b>Đơn giá:</b> <b>{unit_price:,.0f} VND</b>\n\n"
            "╭───────────────────────╮\n"
            f"  💳 <b>TỔNG CẦN TRẢ:</b> <b>{total_price:,.0f} VND</b>\n"
            f"  👛 <b>Số dư hiện tại:</b> <b>{balance:,.0f} VND</b>\n"
            f"  🔴 <b>Còn thiếu:</b> <b>{missing:,.0f} VND</b>\n"
            "╰───────────────────────╯"
            f"{extra_str}\n\n"
            "👇 <i>Bấm nạp tiền bên dưới để tạo mã QR nạp đúng số tiền còn thiếu:</i>"
        )
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"💳 Nạp ngay {missing:,.0f} VND",
                        callback_data=f"dep_amt:{int(missing)}"
                    )
                ],
                [
                    InlineKeyboardButton(text="❌ Hủy bỏ giao dịch", callback_data="confirm_buy_no")
                ]
            ]
        )
    else:
        rem_balance = balance - total_price
        text = (
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
            "     🛒 <b>XÁC NHẬN MUA HÀNG</b> 🛒\n"
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
            f"📦 <b>Sản phẩm:</b> <b>{product_name}</b>\n"
            f"🔢 <b>Số lượng:</b> <b>{quantity}</b>\n"
            f"💰 <b>Đơn giá:</b> <b>{unit_price:,.0f} VND</b>\n\n"
            "╭───────────────────────╮\n"
            f"  💳 <b>TỔNG THANH TOÁN:</b> <b>{total_price:,.0f} VND</b>\n"
            f"  👛 <b>Số dư hiện tại:</b> <b>{balance:,.0f} VND</b>\n"
            f"  💵 <b>Số dư còn lại:</b> <b>{rem_balance:,.0f} VND</b>\n"
            "╰───────────────────────╯"
            f"{extra_str}\n\n"
            "⚡ <i>Nhấn nút bên dưới để hệ thống xuất tài khoản tự động ngay lập tức!</i>"
        )
        kb = get_confirm_purchase_keyboard(product_id)

    if hasattr(target_msg, "edit_text"):
        await target_msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await target_msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(BuyState.waiting_for_confirmation, F.data == "confirm_buy_yes")
async def handle_confirm_buy_yes(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    current_user: User
):
    data = await state.get_data()
    await state.clear()

    await callback.message.edit_text("⏳ <i>Đang xử lý đơn hàng và kết nối máy chủ kho Canboso... Vui lòng không tắt hoặc thao tác lặp lại...</i>", parse_mode="HTML")

    res = await order_service.create_purchase_order(
        session=session,
        telegram_id=current_user.telegram_id,
        product_id=data["product_id"],
        quantity=data.get("quantity", 1),
        customer_email=data.get("customer_email"),
        customer_accounts=data.get("customer_accounts"),
        slot_months=data.get("slot_months")
    )

    if not res.get("success"):
        error_msg = res.get("message", "Giao dịch không thành công.")
        await callback.message.edit_text(
            f"❌ <b>ĐẶT HÀNG THẤT BẠI</b>\n\n"
            f"Lý do: <i>{error_msg}</i>\n\n"
            f"💰 Số dư ví hiện tại của bạn: <b>{res.get('user_balance', current_user.balance):,.0f} VND</b>",
            parse_mode="HTML"
        )
        return

    # Purchase success! Deliver accounts
    delivery_accounts = res.get("delivery_data", [])
    acc_text = ""
    for i, acc in enumerate(delivery_accounts, 1):
        u = acc.get("user") or ""
        p = acc.get("password") or ""
        mail = acc.get("verifyEmail") or ""
        exp = acc.get("expiryText") or ""
        oth = acc.get("otherInfo") or ""

        acc_text += f"\n<b>📦 Tài khoản #{i}:</b>\n"
        if u:
            acc_text += f"• Tài khoản / Email: <code>{u}</code>\n"
        if p:
            acc_text += f"• Mật khẩu: <code>{p}</code>\n"
        if mail:
            acc_text += f"• Email xác minh: <code>{mail}</code>\n"
        if exp:
            acc_text += f"• Hạn dùng: <code>{exp}</code>\n"
        if oth:
            acc_text += f"• Ghi chú: <code>{oth}</code>\n"

    success_msg = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "   🎉 <b>GIAO DỊCH THÀNH CÔNG!</b> 🎉\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"🆔 <b>Mã đơn hàng:</b> <code>{res['order_code']}</code>\n"
        f"📦 <b>Sản phẩm:</b> <b>{res['product_name']}</b> (x{res['quantity']})\n"
        f"💰 <b>Đã thanh toán:</b> <b>{res['sell_price']:,.0f} VND</b>\n"
        f"👛 <b>Số dư còn lại:</b> <b>{res['user_balance']:,.0f} VND</b>\n\n"
        "╭───────────────────────╮\n"
        "  🔐 <b>THÔNG TIN TÀI KHOẢN BÀN GIAO:</b>\n"
        "╰───────────────────────╯"
        f"{acc_text or '\n<i>(Đơn hàng kích hoạt theo email/slot. Vui lòng kiểm tra email của bạn hoặc mục Lịch sử đơn hàng)</i>'}\n\n"
        "🛡️ <i>Đơn hàng được bảo hành 1 đổi 1. Bấm vào mã đơn hàng để sao chép khi cần hỗ trợ!</i>"
    )

    await callback.message.edit_text(success_msg, parse_mode="HTML")
    await callback.answer("Mua hàng thành công!", show_alert=True)


@router.callback_query(BuyState.waiting_for_confirmation, F.data == "confirm_buy_no")
async def handle_confirm_buy_no(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Đã hủy thao tác mua hàng.", parse_mode="HTML")
    await callback.answer("Đã hủy đơn hàng.")
