from aiogram import Router, F
from aiogram.types import Message
from backend.app.models.models import User

router = Router(name="account")


@router.message(F.text == "👤 Tài khoản")
async def show_account(message: Message, current_user: User):
    user_status = "🔴 Bị khóa" if current_user.is_banned else "🟢 Hoạt động"
    role_text = "👑 Quản trị viên (Admin)" if current_user.role == "admin" else "👤 Thành viên"
    join_date = current_user.created_at.strftime("%d/%m/%Y") if current_user.created_at else "N/A"

    # Loyalty tier
    tier = "🥉 Đồng (Member)"
    if current_user.total_spent >= 5000000:
        tier = "💎 Kim Cương (VIP 3)"
    elif current_user.total_spent >= 2000000:
        tier = "🥇 Vàng (VIP 2)"
    elif current_user.total_spent >= 500000:
        tier = "🥈 Bạc (VIP 1)"

    text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "      👤 <b>HỒ SƠ KHÁCH HÀNG VIP</b> 👤\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"🏷️ <b>Họ và tên:</b> <b>{message.from_user.full_name}</b>\n"
        f"🆔 <b>Telegram ID:</b> <code>{current_user.telegram_id}</code>\n"
        f"🔖 <b>Username:</b> @{current_user.username or 'Không có'}\n"
        f"🎖️ <b>Hạng thành viên:</b> <b>{tier}</b>\n"
        f"👑 <b>Quyền hạn:</b> {role_text}\n"
        f"⚡ <b>Trạng thái:</b> {user_status}\n"
        f"📅 <b>Ngày tham gia:</b> {join_date}\n\n"
        "╭───────────────────────╮\n"
        "  💰 <b>TỔNG QUAN TÀI CHÍNH:</b>\n"
        f"  • Số dư khả dụng: <b>{current_user.balance:,.0f} VND</b>\n"
        f"  • Tổng đã chi tiêu: <b>{current_user.total_spent:,.0f} VND</b>\n"
        f"  • Tổng đơn hàng: <b>{current_user.total_orders}</b> đơn\n"
        "╰───────────────────────╯\n\n"
        "🔒 <i>Dữ liệu tài khoản được bảo mật an toàn 100%.</i>"
    )

    await message.answer(text, parse_mode="HTML")
