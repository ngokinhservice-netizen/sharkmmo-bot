import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, Order, PaymentTransaction, ProductCache, utcnow
from backend.app.services.canboso import canboso_client
from backend.app.services.product_sync import sync_canboso_products
from backend.app.payments.payment_service import payment_service
from backend.app.core.config import settings
from backend.app.services.brand_catalog import BRANDS_LAYOUT, BRANDS_DICT
from backend.app.services.custom_emoji_store import (
    get_custom_emoji_id,
    set_custom_emoji,
    bulk_set_custom_emojis,
    get_all_custom_emojis
)

logger = logging.getLogger("sharkmmo.admin_bot")
router = Router(name="admin_bot")


def is_admin(user: User) -> bool:
    return user.role == "admin" or user.telegram_id in settings.ADMIN_IDS


@router.message(Command("admin"))
async def handle_admin_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền truy cập bảng quản trị Admin.")
        return

    # Aggregate stats
    users_count = await session.scalar(select(func.count(User.id))) or 0
    orders_count = await session.scalar(select(func.count(Order.id))) or 0
    completed_orders = await session.scalar(select(func.count(Order.id)).where(Order.status == "completed")) or 0
    total_rev = await session.scalar(select(func.sum(Order.sell_price)).where(Order.status == "completed")) or 0.0
    total_profit = await session.scalar(select(func.sum(Order.profit)).where(Order.status == "completed")) or 0.0
    pending_deposits = await session.scalar(select(func.count(PaymentTransaction.id)).where(PaymentTransaction.status == "pending")) or 0

    text = (
        f"👑 <b>BẢNG ĐIỀU KHIỂN QUẢN TRỊ SHARKMMO</b>\n\n"
        f"👥 Tổng khách hàng: <b>{users_count}</b>\n"
        f"📦 Tổng đơn hàng: <b>{orders_count}</b> (Thành công: <b>{completed_orders}</b>)\n"
        f"💰 Tổng doanh thu: <b>{total_rev:,.0f} VND</b>\n"
        f"📈 Lợi nhuận gộp: <b>{total_profit:,.0f} VND</b>\n"
        f"⏳ Yêu cầu nạp chờ duyệt: <b>{pending_deposits}</b>\n\n"
        f"🛠️ <b>Lệnh nhanh dành cho Admin:</b>\n"
        f"• <code>/balance</code> : Kiểm tra số dư kho nguồn Canboso\n"
        f"• <code>/sync</code> : Đồng bộ lại sản phẩm từ Canboso\n"
        f"• <code>/stats</code> : Báo cáo thống kê chi tiết\n"
        f"• Web Admin Panel: <i>Truy cập Dashboard Next.js</i>"
    )

    await message.answer(text, parse_mode="HTML")


@router.message(Command("balance"))
async def handle_balance_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền quản trị.")
        return

    await message.answer("⏳ Đang truy vấn số dư nguồn từ Canboso API...")
    try:
        source_bal = await canboso_client.get_balance(force_refresh=True)
        bal_text = source_bal.balanceText or f"{source_bal.balance:,.0f} {source_bal.walletCurrency or 'VND'}"
        usdt_text = f"{source_bal.usdtBalance} USDT" if source_bal.usdtBalance else "0 USDT"

        # Customer wallet total
        total_cust_bal = await session.scalar(select(func.sum(User.balance))) or 0.0

        alert_msg = ""
        bal_vnd = source_bal.balanceVnd or source_bal.balance
        if bal_vnd < settings.SOURCE_BALANCE_ALERT_THRESHOLD:
            alert_msg = f"\n⚠️ <b>CẢNH BÁO:</b> Số dư nguồn Canboso đang thấp hơn {settings.SOURCE_BALANCE_ALERT_THRESHOLD:,.0f} VND. Vui lòng nạp thêm tiền vào kho Canboso!"

        text = (
            f"💼 <b>BÁO CÁO SỐ DƯ KHO NGUỒN & HỆ THỐNG</b>\n\n"
            f"🏦 <b>Số dư Canboso API:</b>\n"
            f"• Số dư: <b>{bal_text}</b>\n"
            f"• USDT: <b>{usdt_text}</b>\n"
            f"• Cập nhật: {source_bal.updatedAt or 'Vừa xong'}"
            f"{alert_msg}\n\n"
            f"👥 <b>Số dư ví khách hàng (SHARKMMO):</b>\n"
            f"• Tổng số dư ví thành viên: <b>{total_cust_bal:,.0f} VND</b>\n"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Lỗi truy vấn Canboso balance: {str(e)}")


@router.message(Command("sync"))
async def handle_sync_cmd(message: Message, current_user: User, session: AsyncSession):
    if not is_admin(current_user):
        await message.answer("⛔ Bạn không có quyền quản trị.")
        return

    await message.answer("⏳ Đang đồng bộ danh mục và sản phẩm từ Canboso API...")
    try:
        result = await sync_canboso_products(session, force_refresh=True)
        await message.answer(
            f"✅ <b>ĐỒNG BỘ HOÀN TẤT!</b>\n\n"
            f"• Tổng sản phẩm nguồn: <b>{result.get('total')}</b>\n"
            f"• Thêm mới: <b>{result.get('added')}</b>\n"
            f"• Cập nhật giá & kho: <b>{result.get('updated')}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Đồng bộ thất bại: {str(e)}")


@router.callback_query(F.data.startswith("adm_approve_dep:"))
async def handle_admin_approve_deposit(callback: CallbackQuery, session: AsyncSession, current_user: User):
    if not is_admin(current_user):
        await callback.answer("Bạn không có quyền admin.", show_alert=True)
        return

    tx_id = int(callback.data.split("adm_approve_dep:", 1)[1])
    res = await payment_service.confirm_payment(
        session=session,
        transaction_id=tx_id,
        confirmed_by=f"admin_{current_user.telegram_id}"
    )

    if res.get("success"):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(
            f"✅ Đã duyệt nạp tiền: <b>{res.get('transaction_code')}</b> (+{res.get('amount', 0):,.0f} VND) cho khách <code>{res.get('telegram_id')}</code>.",
            parse_mode="HTML"
        )
        await callback.answer("Duyệt thành công!")
    else:
        await callback.answer(f"Lỗi: {res.get('message')}", show_alert=True)


@router.callback_query(F.data.startswith("adm_reject_dep:"))
async def handle_admin_reject_deposit(callback: CallbackQuery, session: AsyncSession, current_user: User):
    if not is_admin(current_user):
        await callback.answer("Bạn không có quyền admin.", show_alert=True)
        return

    tx_id = int(callback.data.split("adm_reject_dep:", 1)[1])
    res = await payment_service.reject_payment(
        session=session,
        transaction_id=tx_id,
        rejected_by=f"admin_{current_user.telegram_id}"
    )

    if res.get("success"):
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"❌ Đã từ chối giao dịch #{tx_id}.", parse_mode="HTML")
        await callback.answer("Đã từ chối giao dịch.")
    else:
        await callback.answer(f"Lỗi: {res.get('message')}", show_alert=True)


@router.message(Command("set_emoji"))
async def handle_set_emoji_cmd(message: Message, current_user: User):
    if not is_admin(current_user):
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "📖 <b>Cách dùng:</b> <code>/set_emoji &lt;slug&gt; [gửi kèm sticker/emoji hoặc nhập ID]</code>\n"
            "Ví dụ: <code>/set_emoji adobe 5368324170671202288</code>\n"
            "Hoặc: <code>/set_emoji adobe</code> và dán emoji logo Adobe vào tin nhắn.",
            parse_mode="HTML"
        )
        return

    slug = parts[1].strip().lower()
    if slug not in BRANDS_DICT:
        await message.answer(
            f"⚠️ Không tìm thấy thương hiệu <code>{slug}</code>.\n"
            f"Ví dụ các slug hợp lệ: <code>adobe</code>, <code>antigravity</code>, <code>chatgpt</code>, <code>canva</code>, <code>capcut</code>, ...",
            parse_mode="HTML"
        )
        return

    emoji_id = None
    if message.entities:
        for ent in message.entities:
            if ent.type == "custom_emoji":
                emoji_id = ent.custom_emoji_id
                break

    if not emoji_id and len(parts) >= 3:
        raw_id = parts[2].strip()
        if raw_id.isdigit():
            emoji_id = raw_id

    if not emoji_id:
        await message.answer("❌ Vui lòng đính kèm một Telegram Custom Emoji hoặc nhập mã ID số của emoji.")
        return

    set_custom_emoji(slug, emoji_id)
    await message.answer(
        f"✅ <b>ĐÃ CẬP NHẬT CUSTOM EMOJI!</b>\n\n"
        f"• Thương hiệu: <b>{BRANDS_DICT[slug]['name']}</b> (<code>{slug}</code>)\n"
        f"• Emoji ID: <code>{emoji_id}</code>\n\n"
        f"Bàn phím danh mục thương hiệu đã được cập nhật hiển thị logo 100%!",
        parse_mode="HTML"
    )


@router.message(Command("pack"))
async def handle_pack_cmd(message: Message, current_user: User):
    if not is_admin(current_user):
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "📖 <b>Cách dùng:</b> <code>/pack &lt;tên_pack_hoặc_link&gt;</code>\n"
            "Ví dụ: <code>/pack https://t.me/addemoji/BrandsPack</code>\n"
            "Hoặc: <code>/pack BrandsPack</code>",
            parse_mode="HTML"
        )
        return

    raw_pack = parts[1].strip()
    pack_name = raw_pack.rstrip("/").split("/")[-1]

    try:
        sticker_set = await message.bot.get_sticker_set(pack_name)
        stickers = sticker_set.stickers or []
        await message.answer(
            f"📦 <b>TÌM THẤY GÓI EMOJI:</b> <b>{sticker_set.title}</b>\n"
            f"• Tên pack: <code>{sticker_set.name}</code>\n"
            f"• Loại: <code>{sticker_set.sticker_type}</code>\n"
            f"• Tổng số: <b>{len(stickers)}</b> sticker/emoji\n\n"
            f"Gói này đã sẵn sàng để bot sử dụng hiển thị các logo trên nút bấm!",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Không thể tải gói emoji <code>{pack_name}</code>: {str(e)}", parse_mode="HTML")


@router.message(Command("list_emojis"))
async def handle_list_emojis_cmd(message: Message, current_user: User):
    if not is_admin(current_user):
        return
    emojis = get_all_custom_emojis()
    if not emojis:
        await message.answer("ℹ️ Chưa có Custom Emoji nào được gán.")
        return

    lines = []
    for slug, eid in sorted(emojis.items()):
        name = BRANDS_DICT.get(slug, {}).get("name", slug)
        lines.append(f"• <b>{name}</b> (<code>{slug}</code>): <code>{eid}</code>")

    await message.answer(
        f"📋 <b>DANH SÁCH {len(emojis)} CUSTOM EMOJI ĐÃ CẤU HÌNH:</b>\n\n" + "\n".join(lines),
        parse_mode="HTML"
    )


@router.message(F.entities)
async def handle_admin_custom_emoji_sniffer(message: Message, current_user: User):
    """
    Automatically detects any custom emojis sent by the admin
    and prints their IDs for instant one-click assignment.
    """
    if not is_admin(current_user):
        return
    if message.text and message.text.startswith("/"):
        return

    detected = []
    for ent in (message.entities or []):
        if ent.type == "custom_emoji" and ent.custom_emoji_id:
            detected.append(ent.custom_emoji_id)

    if not detected:
        return

    unique_ids = list(dict.fromkeys(detected))
    lines = [f"<code>{cid}</code>" for cid in unique_ids[:15]]
    more_txt = f"\n...và thêm {len(unique_ids) - 15} emoji nữa." if len(unique_ids) > 15 else ""

    await message.answer(
        f"🎯 <b>Phát hiện {len(unique_ids)} Custom Emoji từ tin nhắn:</b>\n"
        + "\n".join(lines)
        + more_txt
        + f"\n\n👉 Để gán cho thương hiệu, dùng: <code>/set_emoji &lt;slug&gt; &lt;ID&gt;</code>",
        parse_mode="HTML"
    )

