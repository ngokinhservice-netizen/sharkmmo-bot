from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, Order

router = Router(name="orders")


@router.message(F.text == "🧾 Lịch sử đơn hàng")
async def show_order_history(message: Message, current_user: User, session: AsyncSession):
    q = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .order_by(Order.id.desc())
        .limit(10)
    )
    res = await session.execute(q)
    orders = res.scalars().all()

    if not orders:
        await message.answer(
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
            "   🧾 <b>LỊCH SỬ ĐƠN HÀNG TRỐNG</b> 🧾\n"
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
            "Bạn chưa mua sản phẩm nào tại SHARKMMO.\n"
            "👉 Hãy nhấn <b>🛍️ Mua sản phẩm</b> để trải nghiệm giao hàng tự động ngay nhé!",
            parse_mode="HTML"
        )
        return

    buttons = []
    text_lines = [
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "   🧾 <b>LỊCH SỬ ĐƠN HÀNG GẦN ĐÂY</b> 🧾\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
    ]

    for ord in orders:
        st_icon = "🟢 Thành công" if ord.status == "completed" else ("🔴 Thất bại" if ord.status == "failed" else "⏳ Đang xử lý")
        date_str = ord.created_at.strftime("%d/%m %H:%M") if ord.created_at else ""
        text_lines.append(f"• <code>{ord.order_code}</code> | <b>{ord.product_name}</b> x{ord.quantity}\n  💵 {ord.sell_price:,.0f} VND — {st_icon} ({date_str})")

        if ord.status == "completed" and ord.delivery_data:
            buttons.append([
                InlineKeyboardButton(
                    text=f"🔑 Xem tài khoản: {ord.order_code}",
                    callback_data=f"view_ord:{ord.id}"
                )
            ])

    text = "\n".join(text_lines)
    text += "\n\n<i>👇 Nhấn vào nút bên dưới để xem lại thông tin tài khoản đã nhận:</i>"

    await message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("view_ord:"))
async def view_order_detail(callback: CallbackQuery, session: AsyncSession, current_user: User):
    order_id = int(callback.data.split("view_ord:", 1)[1])
    q = select(Order).where(Order.id == order_id, Order.user_id == current_user.id)
    res = await session.execute(q)
    order = res.scalars().first()

    if not order:
        await callback.answer("Không tìm thấy đơn hàng.", show_alert=True)
        return

    delivery_accounts = order.delivery_data or []
    accounts_text = ""
    for i, acc in enumerate(delivery_accounts, 1):
        u = acc.get("user") or ""
        p = acc.get("password") or ""
        mail = acc.get("verifyEmail") or ""
        exp = acc.get("expiryText") or ""
        oth = acc.get("otherInfo") or ""

        accounts_text += f"\n<b>📦 Tài khoản #{i}:</b>\n"
        if u:
            accounts_text += f"• User / Email: <code>{u}</code>\n"
        if p:
            accounts_text += f"• Pass: <code>{p}</code>\n"
        if mail:
            accounts_text += f"• Mail xác thực: <code>{mail}</code>\n"
        if exp:
            accounts_text += f"• Hạn sử dụng: <code>{exp}</code>\n"
        if oth:
            accounts_text += f"• Thông tin thêm: <code>{oth}</code>\n"

    if not accounts_text:
        accounts_text = "\n<i>(Đơn hàng đang chờ nhân viên đối soát hoặc không có thông tin tài khoản)</i>\n"

    msg = (
        f"🦈 <b>CHI TIẾT ĐƠN HÀNG: {order.order_code}</b>\n\n"
        f"📦 Sản phẩm: <b>{order.product_name}</b>\n"
        f"🔢 Số lượng: <b>{order.quantity}</b>\n"
        f"💰 Tổng tiền: <b>{order.sell_price:,.0f} VND</b>\n"
        f"📅 Ngày mua: {order.created_at.strftime('%d/%m/%Y %H:%M:%S') if order.created_at else ''}\n"
        f"🆔 Mã nguồn Canboso: <code>{order.canboso_order_code or 'N/A'}</code>\n"
        f"────────────────────\n"
        f"<b>🔐 THÔNG TIN BÀN GIAO:</b>\n"
        f"{accounts_text}\n"
        f"────────────────────\n"
        f"💡 <i>Gợi ý: Nhấn vào các thông tin trong ô mã để sao chép nhanh!</i>"
    )

    await callback.message.answer(msg, parse_mode="HTML")
    await callback.answer()
