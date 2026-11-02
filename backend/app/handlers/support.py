from aiogram import Router, F
from aiogram.types import Message

router = Router(name="support")


@router.message(F.text == "💬 Hỗ trợ")
async def show_support(message: Message):
    text = (
        f"💬 <b>TRUNG TÂM HỖ TRỢ KHÁCH HÀNG SHARKMMO</b>\n\n"
        f"Bạn cần trợ giúp về đơn hàng, nạp tiền hoặc bảo hành sản phẩm?\n\n"
        f"🕒 <b>Thời gian làm việc:</b> 08:00 — 23:30 hàng ngày\n\n"
        f"📞 <b>Kênh liên hệ hỗ trợ trực tiếp:</b>\n"
        f"• Telegram Admin: @SharkMMO_Support\n"
        f"• Kênh thông báo: @SharkMMO_Channel\n"
        f"• Nhóm cộng đồng: @SharkMMO_Chat\n\n"
        f"🛡️ <b>CHÍNH SÁCH BẢO HÀNH:</b>\n"
        f"1. Bảo hành 1 đổi 1 hoặc hoàn tiền 100% nếu tài khoản lỗi ngay sau khi nhận.\n"
        f"2. Không bảo hành các trường hợp vi phạm chính sách của nhà cung cấp (đổi mật khẩu, chia sẻ trái phép).\n"
        f"3. Khi cần bảo hành, vui lòng gửi kèm <b>Mã đơn hàng (SHARK-...)</b> để được xử lý nhanh nhất.\n\n"
        f"🦈 <i>SHARKMMO — Cam kết chất lượng & uy tín hàng đầu!</i>"
    )

    await message.answer(text, parse_mode="HTML")
