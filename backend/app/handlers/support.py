from aiogram import Router, F
from aiogram.types import Message

router = Router(name="support")


@router.message(F.text == "💬 Hỗ trợ")
async def show_support(message: Message):
    text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "   💬 <b>TRUNG TÂM HỖ TRỢ KHÁCH HÀNG</b> 💬\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        "👋 Bạn cần hỗ trợ về đơn hàng, nạp tiền hoặc bảo hành sản phẩm?\n\n"
        "🕒 <b>Thời gian trực hỗ trợ:</b> 08:00 — 23:30 (Hằng ngày)\n\n"
        "╭───────────────────────╮\n"
        "  📞 <b>KÊNH LIÊN HỆ TRỰC TIẾP:</b>\n"
        "  • 👤 Telegram Admin: @SharkMMO_Support\n"
        "  • 📢 Kênh thông báo: @SharkMMO_Channel\n"
        "  • 👥 Nhóm thảo luận: @SharkMMO_Chat\n"
        "╰───────────────────────╯\n\n"
        "🛡️ <b>CHÍNH SÁCH BẢO HÀNH VIP:</b>\n"
        "• <b>1 đổi 1 ngay lập tức</b> nếu tài khoản phát sinh lỗi.\n"
        "• Hỗ trợ đổi mới hoặc hoàn tiền theo quy định bảo hành.\n"
        "• Vui lòng gửi kèm <b>Mã đơn hàng</b> để Admin xử lý nhanh nhất.\n\n"
        "🦈 <i>SHARKMMO — Cam kết chất lượng & uy tín hàng đầu!</i>"
    )

    await message.answer(text, parse_mode="HTML")
