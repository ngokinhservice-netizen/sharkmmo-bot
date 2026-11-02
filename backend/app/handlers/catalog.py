import math
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, distinct, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache
from backend.app.keyboards.menus import (
    get_categories_keyboard,
    get_products_pagination_keyboard,
    get_product_detail_keyboard
)

router = Router(name="catalog")
PAGE_SIZE = 5


@router.message(F.text.in_(["🛍️ Mua sản phẩm", "📦 Danh mục sản phẩm"]))
async def show_categories(message: Message, session: AsyncSession):
    query = (
        select(ProductCache.category, func.count(ProductCache.id))
        .where(ProductCache.is_active == True)
        .group_by(ProductCache.category)
    )
    res = await session.execute(query)
    categories = [f"{cat} ({count})" for cat, count in res.all()]

    if not categories:
        await message.answer(
            "📦 Hiện tại chưa có sản phẩm nào đang hoạt động. Vui lòng quay lại sau!",
            parse_mode="HTML"
        )
        return

    await message.answer(
        "📂 <b>DANH MỤC SẢN PHẨM SHARKMMO</b>\n<i>Vui lòng chọn danh mục bạn muốn xem:</i>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "categories")
async def callback_categories(callback: CallbackQuery, session: AsyncSession):
    query = (
        select(ProductCache.category, func.count(ProductCache.id))
        .where(ProductCache.is_active == True)
        .group_by(ProductCache.category)
    )
    res = await session.execute(query)
    categories = [f"{cat} ({count})" for cat, count in res.all()]

    await callback.message.edit_text(
        "📂 <b>DANH MỤC SẢN PHẨM SHARKMMO</b>\n<i>Vui lòng chọn danh mục bạn muốn xem:</i>",
        reply_markup=get_categories_keyboard(categories),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cat:"))
async def callback_select_category(callback: CallbackQuery, session: AsyncSession):
    # e.g. cat:🤖 AI & Đồ họa (5) -> clean category name
    raw_cat = callback.data.split("cat:", 1)[1]
    cat_clean = raw_cat.rsplit(" (", 1)[0].strip()

    await render_product_page(callback, session, page=1, category=cat_clean)
    await callback.answer()


@router.callback_query(F.data.startswith("page:"))
async def callback_pagination(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    page = int(parts[1])
    category = parts[2] if len(parts) > 2 else None

    await render_product_page(callback, session, page=page, category=category)
    await callback.answer()


@router.callback_query(F.data == "products:page:1")
async def callback_all_products(callback: CallbackQuery, session: AsyncSession):
    await render_product_page(callback, session, page=1, category=None)
    await callback.answer()


async def render_product_page(
    callback: CallbackQuery,
    session: AsyncSession,
    page: int,
    category: Optional[str] = None
):
    base_q = select(ProductCache).where(ProductCache.is_active == True)
    count_q = select(func.count(ProductCache.id)).where(ProductCache.is_active == True)

    if category:
        base_q = base_q.where(ProductCache.category == category)
        count_q = count_q.where(ProductCache.category == category)

    total_count_res = await session.execute(count_q)
    total_items = total_count_res.scalar() or 0
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * PAGE_SIZE
    items_q = base_q.order_by(ProductCache.id.asc()).offset(offset).limit(PAGE_SIZE)
    items_res = await session.execute(items_q)
    products = items_res.scalars().all()

    if not products:
        await callback.message.edit_text(
            f"⚠️ Không có sản phẩm nào trong mục <b>{category or 'Tất cả'}</b>.",
            reply_markup=get_categories_keyboard([]),
            parse_mode="HTML"
        )
        return

    prod_dicts = [
        {
            "product_id": p.product_id,
            "name": p.name,
            "calculated_price": p.calculated_price,
            "available_qty": p.available_qty
        }
        for p in products
    ]

    title = f"🏷️ <b>DANH SÁCH SẢN PHẨM {f'— {category}' if category else ''}</b>"
    body = (
        f"{title}\n"
        f"📄 Trang <b>{page}/{total_pages}</b> (Tổng <b>{total_items}</b> sản phẩm)\n\n"
        f"<i>Nhấn vào sản phẩm bên dưới để xem chi tiết & mua hàng:</i>"
    )

    await callback.message.edit_text(
        body,
        reply_markup=get_products_pagination_keyboard(prod_dicts, page, total_pages, category),
        parse_mode="HTML"
    )


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
        stock_text = "🔴 <b>Hết hàng</b>"

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
            promo_text = "\n🎁 <b>Ưu đãi số lượng lớn:</b>\n" + "\n".join(promo_lines)

    desc = product.description or "Không có mô tả chi tiết."

    card_text = (
        f"🦈 <b>{product.name}</b>\n\n"
        f"🆔 <b>Mã SP:</b> <code>{product.product_id}</code>\n"
        f"📦 <b>Loại SP:</b> <code>{product.product_type}</code>\n"
        f"📂 <b>Danh mục:</b> {product.category}\n"
        f"💰 <b>Giá bán:</b> <b>{product.calculated_price:,.0f} VND</b>\n"
        f"📊 <b>Trạng thái:</b> {stock_text}\n"
        f"🔥 <b>Đã bán:</b> {product.sold_qty}\n"
        f"{promo_text}\n\n"
        f"📝 <b>Mô tả sản phẩm:</b>\n"
        f"<i>{desc}</i>\n\n"
        f"⚡ <i>Hệ thống giao tài khoản tự động ngay sau khi xác nhận thanh toán!</i>"
    )

    await callback.message.edit_text(
        card_text,
        reply_markup=get_product_detail_keyboard(product.product_id, is_available=in_stock),
        parse_mode="HTML"
    )
    await callback.answer()
