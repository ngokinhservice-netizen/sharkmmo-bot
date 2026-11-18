import math
from typing import Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache, User
from backend.app.keyboards.menus import (
    get_store_catalog_keyboard,
    get_product_detail_keyboard,
    get_main_menu
)

router = Router(name="catalog")
STORE_PAGE_SIZE = 12


async def render_store_view(
    event: Union[Message, CallbackQuery],
    session: AsyncSession,
    tag: Optional[str] = None,
    page: int = 1
):
    """
    Renders the store UI matching Image 2:
    - Top: 3-column quick brand tags (Canva, Capcut, ChatGPT, YouTube, etc.)
    - Middle: Full-width product buttons with {icon} {name} | {price} | 📦 {stock}
    - Bottom: Refresh & Home / Support controls
    """
    base_q = select(ProductCache).where(ProductCache.is_active == True)
    count_q = select(func.count(ProductCache.id)).where(ProductCache.is_active == True)

    if tag:
        pattern = f"%{tag}%"
        cond = or_(
            ProductCache.name.ilike(pattern),
            ProductCache.description.ilike(pattern),
            ProductCache.category.ilike(pattern)
        )
        base_q = base_q.where(cond)
        count_q = count_q.where(cond)

    # In-stock products first, then highest available quantity, then most sold
    in_stock_order = case((ProductCache.available_qty > 0, 0), else_=1)
    base_q = base_q.order_by(
        in_stock_order,
        ProductCache.available_qty.desc(),
        ProductCache.sold_qty.desc(),
        ProductCache.id.asc()
    )

    total_count = (await session.execute(count_q)).scalar() or 0
    total_pages = max(1, math.ceil(total_count / STORE_PAGE_SIZE))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * STORE_PAGE_SIZE
    items_res = await session.execute(base_q.offset(offset).limit(STORE_PAGE_SIZE))
    products = items_res.scalars().all()

    prod_dicts = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "calculated_price": p.calculated_price,
            "available_qty": p.available_qty
        }
        for p in products
    ]

    if tag:
        banner = f"🔥 <b>Mua từ 10+ giảm 20%</b> | 🏷️ <i>{tag} ({total_count} sp)</i>"
    else:
        banner = "🔥 <b>Mua từ 10+ giảm 20%</b>"

    kb = get_store_catalog_keyboard(
        prod_dicts,
        selected_tag=tag,
        page=page,
        total_pages=total_pages
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(banner, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(banner, reply_markup=kb, parse_mode="HTML")


@router.message(F.text.in_(["🛍️ Mua sản phẩm", "📦 Danh mục sản phẩm"]))
async def show_store_home(message: Message, session: AsyncSession):
    await render_store_view(message, session, tag=None, page=1)


@router.callback_query(F.data.startswith("tag:"))
async def handle_tag_filter(callback: CallbackQuery, session: AsyncSession):
    tag = callback.data.split("tag:", 1)[1]
    await render_store_view(callback, session, tag=tag, page=1)


@router.callback_query(F.data.startswith("spage:"))
async def handle_store_pagination(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    page = int(parts[1])
    tag = parts[2] if len(parts) > 2 and parts[2] else None
    await render_store_view(callback, session, tag=tag, page=page)


@router.callback_query(F.data == "refresh_store")
async def handle_refresh_store(callback: CallbackQuery, session: AsyncSession):
    await render_store_view(callback, session, tag=None, page=1)


@router.callback_query(F.data == "home_menu")
async def handle_home_menu(callback: CallbackQuery, session: AsyncSession):
    # Fetch user for balance display
    q = select(User).where(User.telegram_id == callback.from_user.id)
    res = await session.execute(q)
    user = res.scalars().first()
    bal = f"{user.balance:,.0f} VND" if user else "0 VND"

    first_name = callback.from_user.first_name or "Quý khách"
    text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "      🔥 <b>SHARKMMO STORE PRO</b> 🔥\n"
        "   <i>Hệ sinh thái sản phẩm MMO tự động</i>\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"👋 Xin chào <b>{first_name}</b>!\n"
        f"🆔 ID Telegram: <code>{callback.from_user.id}</code>\n"
        f"💰 Số dư ví hiện có: <b>{bal}</b>\n\n"
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
        "👇 <i>Sử dụng các nút menu bên dưới để bắt đầu:</i>"
    )
    # Give a button to open store
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Mở Cửa Hàng Sản Phẩm", callback_data="refresh_store")],
        [InlineKeyboardButton(text="💰 Nạp Tiền Vào Ví", callback_data="dep_amt:50000"),
         InlineKeyboardButton(text="💬 Hỗ Trợ 24/7", callback_data="support_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "support_menu")
async def handle_support_menu(callback: CallbackQuery):
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛍️ Cửa hàng", callback_data="refresh_store"),
            InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
        ]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("prod:"))
async def callback_product_detail(callback: CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("prod:", 1)[1]
    q = select(ProductCache).where(ProductCache.product_id == product_id)
    res = await session.execute(q)
    product = res.scalars().first()

    if not product:
        await callback.answer("Sản phẩm không tìm thấy hoặc đã bị xóa.", show_alert=True)
        return

    # Check stock
    in_stock = True
    if product.available_qty is not None and product.available_qty <= 0:
        in_stock = False

    stock_text = f"🟢 Còn hàng: <b>{product.available_qty}</b> cái" if product.available_qty is not None else "🟢 Sẵn sàng cung cấp"
    if not in_stock:
        stock_text = "🔴 <b>Tạm hết hàng</b>"

    # Promotions text
    promo_text = ""
    if product.promotions:
        promo_lines = []
        for promo in product.promotions:
            if promo.get("type") == "bulk_discount":
                line = f"• Mua từ {promo.get('minQty', 0):.0f} cái: Giảm {promo.get('percent', 0)}%"
                if promo.get("bonusQty"):
                    line += f" + Tặng {promo.get('bonusQty')} cái"
                promo_lines.append(line)
        if promo_lines:
            promo_text = "\n🎁 <b>ƯU ĐÃI SỐ LƯỢNG LỚN:</b>\n" + "\n".join(promo_lines)

    desc = product.description or "Không có mô tả chi tiết."

    card_text = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "       💎 <b>CHI TIẾT SẢN PHẨM</b> 💎\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        f"📌 <b>Tên sản phẩm:</b> <b>{product.name}</b>\n"
        f"📂 <b>Danh mục:</b> <code>{product.category}</code>\n"
        f"🆔 <b>Mã sản phẩm:</b> <code>{product.product_id}</code>\n\n"
        "╭───────────────────────╮\n"
        f"  💰 <b>ĐƠN GIÁ:</b> <b>{product.calculated_price:,.0f} VND</b>\n"
        f"  📊 <b>TRẠNG THÁI:</b> {stock_text}\n"
        f"  🔥 <b>ĐÃ BÁN:</b> <b>{product.sold_qty}</b> lượt\n"
        "╰───────────────────────╯"
        f"{promo_text}\n\n"
        "📝 <b>MÔ TẢ SẢN PHẨM:</b>\n"
        f"<i>{desc}</i>\n\n"
        "⚡ <i>Hệ thống tự động giao hàng tức thì sau khi xác nhận thanh toán!</i>"
    )

    await callback.message.edit_text(
        card_text,
        reply_markup=get_product_detail_keyboard(product.product_id, is_available=in_stock),
        parse_mode="HTML"
    )
    await callback.answer()
