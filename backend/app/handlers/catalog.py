import math
import logging
from typing import Optional, Union
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache, User
from backend.app.services.brand_catalog import (
    BRANDS_DICT,
    get_brand_products,
    get_featured_store_products,
    match_product_to_brand
)
from backend.app.services.product_sync import sync_canboso_products
from backend.app.keyboards.menus import (
    get_brand_catalog_keyboard,
    get_brand_packages_keyboard,
    get_product_detail_keyboard,
    get_main_menu
)

logger = logging.getLogger("sharkmmo.catalog")
router = Router(name="catalog")

BRAND_PAGE_SIZE = 15


async def render_catalog_home(
    event: Union[Message, CallbackQuery],
    session: AsyncSession
):
    """
    Renders the Canboso brand catalog layout matching Image 3:
    - 3-column grid of all 62 brands
    - Featured / Hot products shelf below the brand grid
    - Bottom button: 🔄 Cập nhật sản phẩm
    """
    featured = await get_featured_store_products(session, limit=7)
    feat_dicts = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "calculated_price": p.calculated_price,
            "available_qty": p.available_qty
        }
        for p in featured
    ]

    banner = (
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
        "      🔥 <b>SHARKMMO STORE — KHO SẢN PHẨM SỐ MMO</b> 🔥\n"
        "   <i>Tự động giao hàng 24/7 | Nạp tiền VietQR duyệt tức thì</i>\n"
        "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
        "👇 <b>Bấm chọn thương hiệu bên dưới để xem các gói dịch vụ:</b>"
    )

    kb = get_brand_catalog_keyboard(feat_dicts)

    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(banner, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await event.message.answer(banner, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(banner, reply_markup=kb, parse_mode="HTML")


async def render_brand_packages(
    event: Union[Message, CallbackQuery],
    session: AsyncSession,
    slug: str,
    page: int = 1
):
    """
    Renders packages inside a selected brand ("ấn vào trong mới ra các gói khác"):
    - Displays full list of package variants for the brand
    - Stock quantity and price for each package
    - Pagination if more than BRAND_PAGE_SIZE packages
    - Back to brand catalog button
    """
    meta = BRANDS_DICT.get(slug, {
        "name": slug.title(),
        "slug": slug,
        "icon": "📦"
    })

    products, total_count, total_pages = await get_brand_products(
        session,
        slug=slug,
        page=page,
        page_size=BRAND_PAGE_SIZE
    )

    icon = meta.get("icon", "📦")
    name = meta.get("name", slug.title())

    if total_count == 0:
        text = (
            f"{icon} ━━━━━━━━━━━━━━━━━━━━━━ {icon}\n"
            f"       📂 <b>THƯƠNG HIỆU: {name.upper()}</b>\n"
            f"{icon} ━━━━━━━━━━━━━━━━━━━━━━ {icon}\n\n"
            "⚠️ <i>Hiện tại các gói của thương hiệu này đang tạm hết hàng hoặc đang cập nhật dữ liệu.</i>\n\n"
            "👉 Quý khách vui lòng chọn thương hiệu khác hoặc bấm cập nhật sản phẩm."
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Quay lại danh mục", callback_data="store_brands"),
                InlineKeyboardButton(text="🔄 Cập nhật", callback_data=f"b:{slug}")
            ],
            [
                InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
            ]
        ])
    else:
        text = (
            f"{icon} ━━━━━━━━━━━━━━━━━━━━━━ {icon}\n"
            f"       📂 <b>THƯƠNG HIỆU: {name.upper()}</b>\n"
            f"{icon} ━━━━━━━━━━━━━━━━━━━━━━ {icon}\n\n"
            f"✨ <i>Tìm thấy <b>{total_count}</b> gói dịch vụ sẵn sàng:</i>\n"
            f"<i>(Trang {page}/{total_pages} — Bấm vào gói để xem chi tiết & mua)</i>"
        )
        prod_dicts = [
            {
                "product_id": p.product_id,
                "name": p.name,
                "calculated_price": p.calculated_price,
                "available_qty": p.available_qty
            }
            for p in products
        ]
        kb = get_brand_packages_keyboard(
            slug=slug,
            products=prod_dicts,
            page=page,
            total_pages=total_pages
        )

    if isinstance(event, CallbackQuery):
        try:
            await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await event.message.answer(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text.in_(["🛍️ Mua sản phẩm", "📦 Danh mục sản phẩm"]))
async def show_store_home(message: Message, session: AsyncSession):
    await render_catalog_home(message, session)


@router.callback_query(F.data.in_(["store_brands", "categories"]))
async def handle_store_brands(callback: CallbackQuery, session: AsyncSession):
    await render_catalog_home(callback, session)


@router.callback_query(F.data == "refresh_store")
async def handle_refresh_store(callback: CallbackQuery, session: AsyncSession):
    try:
        await callback.answer("⏳ Đang đồng bộ sản phẩm mới nhất từ hệ thống...", show_alert=False)
        await sync_canboso_products(session, force_refresh=True)
    except Exception as e:
        logger.warning(f"Refresh store sync warning: {e}")
    await render_catalog_home(callback, session)


@router.callback_query(F.data.startswith("b:"))
async def handle_brand_click(callback: CallbackQuery, session: AsyncSession):
    slug = callback.data.split("b:", 1)[1]
    await render_brand_packages(callback, session, slug=slug, page=1)


@router.callback_query(F.data.startswith("bp:"))
async def handle_brand_pagination(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    slug = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 1
    await render_brand_packages(callback, session, slug=slug, page=page)


# Legacy tag compatibility
@router.callback_query(F.data.startswith("tag:"))
async def handle_legacy_tag(callback: CallbackQuery, session: AsyncSession):
    tag = callback.data.split("tag:", 1)[1].lower()
    slug = match_product_to_brand(tag)
    if slug != "other":
        await render_brand_packages(callback, session, slug=slug, page=1)
    else:
        await render_catalog_home(callback, session)


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

    # Identify brand slug for back navigation
    brand_slug = match_product_to_brand(product.name, product.emoji)

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
        reply_markup=get_product_detail_keyboard(
            product_id=product.product_id,
            brand_slug=brand_slug,
            is_available=in_stock
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "home_menu")
async def handle_home_menu(callback: CallbackQuery, session: AsyncSession):
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
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍️ Mở Cửa Hàng Sản Phẩm", callback_data="store_brands")],
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
            InlineKeyboardButton(text="🛍️ Cửa hàng", callback_data="store_brands"),
            InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
        ]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
