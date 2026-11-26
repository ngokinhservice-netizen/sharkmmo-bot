from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User
from backend.app.keyboards.menus import get_main_menu

router = Router(name="start")

@router.message(CommandStart())
async def handle_start(message: Message, current_user: User):
    first_name = message.from_user.first_name or "Quý khách"
    balance_text = f"{current_user.balance:,.0f} VND"
    text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "      🔥 <b>SHARKMMO STORE PRO</b> 🔥\n"
        "   <i>Hệ sinh thái sản phẩm MMO tự động</i>\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"👋 Xin chào <b>{first_name}</b>!\n"
        f"🆔 ID Telegram: <code>{current_user.telegram_id}</code>\n"
        f"💰 Số dư ví hiện có: <b>{balance_text}</b>\n\n"
        "╭───────────────────────╮\n"
        "  ✨ <b>DỊCH VỤ NỔI BẬT HÀNG ĐẦU:</b>\n"
        "  ├ 🤖 <b>Tài khoản AI:</b> ChatGPT, Claude, Canva Pro\n"
        "  ├ 📱 <b>Tài khoản MXH:</b> Facebook, TikTok, X/Twitter\n"
        "  ├ 🛡️ <b>Mạng & Proxy:</b> Proxy IPv4/IPv6, VPN Cao cấp\n"
        "  └ 🎬 <b>Giải trí số:</b> Netflix, Spotify, YouTube Pre\n"
        "╰───────────────────────╯\n\n"
        "🌟 <b>CAM KẾT DỊCH VỤ:</b>\n"
        "⚡ <b>Giao hàng tự động:</b> Nhận hàng trong 1 giây\n"
        "💳 <b>Nạp tiền VietQR:</b> Tự động duyệt 24/7\n"
        "🔒 <b>Bảo hành uy tín:</b> 1 đổi 1 chu đáo\n\n"
        "👇 <i>Bấm nút bên dưới hoặc menu bàn phím để bắt đầu mua sắm:</i>"
    )
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍️ Mở Cửa Hàng Sản Phẩm", callback_data="store_brands")
        ],
        [
            InlineKeyboardButton(text="💰 Nạp Tiền Vào Ví", callback_data="dep_amt:50000"),
            InlineKeyboardButton(text="💬 Hỗ Trợ 24/7", callback_data="support_menu")
        ]
    ])
    await message.answer(
        text=text,
        reply_markup=inline_kb,
        parse_mode="HTML"
    )
    # Also ensure reply keyboard is active
    await message.answer(
        "📱 <i>Menu phím tắt nhanh bên dưới:</i>",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )
