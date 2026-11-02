from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User
from backend.app.keyboards.menus import get_main_menu, get_categories_keyboard

router = Router(name="start")

START_BANNER = """
🦈 <b>CHÀO MỪNG ĐẾN VỚI SHARKMMO</b> 🦈
<i>"Hệ sinh thái sản phẩm MMO tự động"</i>

🔥 <b>Nền tảng cung cấp tài khoản & công cụ số hàng đầu:</b>
• 🤖 <b>Tài khoản AI:</b> ChatGPT Plus, OpenAI, Claude, Midjourney, Canva Pro
• 📱 <b>Tài khoản MXH:</b> Facebook, TikTok, Instagram, Twitter/X
• 🛡️ <b>Bảo mật & Proxy:</b> Proxy IPv4/IPv6, VPN cao cấp
• 🎬 <b>Giải trí số:</b> Netflix, Spotify, YouTube Premium

✨ <b>Ưu điểm vượt trội:</b>
⚡ Nhận tài khoản tự động ngay sau khi thanh toán
💳 Hỗ trợ nạp tiền tự động qua QR Ngân hàng 24/7
🔒 Bảo hành chu đáo, đối soát minh bạch

👉 <i>Vui lòng chọn tính năng bên dưới để bắt đầu:</i>
"""


@router.message(CommandStart())
async def handle_start(message: Message, current_user: User):
    first_name = message.from_user.first_name or "Quý khách"
    balance_text = f"{current_user.balance:,.0f}đ"
    text = (
        f"Xin chào <b>{first_name}</b>!\n"
        f"💰 Số dư ví của bạn: <b>{balance_text}</b>\n\n"
        f"{START_BANNER}"
    )
    await message.answer(
        text=text,
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
