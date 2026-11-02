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
        f"👤 <b>HỒ SƠ KHÁCH HÀNG SHARKMMO</b>\n\n"
        f"🆔 Telegram ID: <code>{current_user.telegram_id}</code>\n"
        f"🔖 Tên người dùng: @{current_user.username or 'Không có'}\n"
        f"🏷️ Họ và tên: <b>{message.from_user.full_name}</b>\n"
        f"🎖️ Hạng thành viên: <b>{tier}</b>\n"
        f"👑 Quyền hạn: {role_text}\n"
        f"⚡ Trạng thái: {user_status}\n"
        f"📅 Ngày tham gia: {join_date}\n\n"
        f"💰 <b>TỔNG QUAN TÀI CHÍNH:</b>\n"
        f"• Số dư khả dụng: <b>{current_user.balance:,.0f} VND</b>\n"
        f"• Tổng chi tiêu: <b>{current_user.total_spent:,.0f} VND</b>\n"
        f"• Tổng đơn hàng: <b>{current_user.total_orders} đơn</b>\n\n"
        f"🔒 <i>Dữ liệu được mã hóa và bảo vệ an toàn tuyệt đối.</i>"
    )

    await message.answer(text, parse_mode="HTML")
