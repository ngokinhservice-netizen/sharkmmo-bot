import math
from typing import List, Optional, Tuple, Dict, Any
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from backend.app.services.brand_catalog import BRANDS_LAYOUT, BRANDS_DICT, match_product_to_brand


def get_product_icon(name: str) -> str:
    slug = match_product_to_brand(name)
    if slug in BRANDS_DICT:
        return BRANDS_DICT[slug]["icon"]
    n = name.lower()
    if "canva" in n:
        return "🎨"
    if "capcut" in n:
        return "✂️"
    if "chatgpt" in n or "gpt" in n:
        return "🤖"
    if "youtube" in n:
        return "🔴"
    if "claude" in n:
        return "✴️"
    if "codex" in n:
        return "⚙️"
    if "gmail" in n:
        return "✉️"
    if "elevenlabs" in n or "eleven" in n:
        return "🎙️"
    if "notion" in n:
        return "📝"
    if "vpn" in n or "hma" in n or "proxy" in n:
        return "🛡️"
    if "cursor" in n:
        return "📦"
    if "suno" in n:
        return "🎵"
    if "zoom" in n:
        return "📹"
    if "grok" in n:
        return "⚡"
    if "deepseek" in n:
        return "🐋"
    if "gemini" in n:
        return "✨"
    if "netflix" in n:
        return "🍿"
    if "office" in n or "365" in n or "ms365" in n:
        return "💼"
    if "duolingo" in n:
        return "🦉"
    if "muse" in n:
        return "🎼"
    return "🔹"


def format_mmo_price(val: float) -> str:
    if val >= 1000:
        k_val = int(round(val / 1000))
        return f"{k_val}k"
    return f"{int(val)}đ"


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Standard Vietnamese 8-button reply menu:
    - 🛍️ Mua sản phẩm
    - 📦 Danh mục sản phẩm
    - 🔎 Tìm kiếm
    - 💰 Ví của tôi
    - 🧾 Lịch sử đơn hàng
    - 🎁 Khuyến mãi
    - 👤 Tài khoản
    - 💬 Hỗ trợ
    """
    kb = [
        [
            KeyboardButton(text="🛍️ Mua sản phẩm"),
            KeyboardButton(text="📦 Danh mục sản phẩm")
        ],
        [
            KeyboardButton(text="🔎 Tìm kiếm"),
            KeyboardButton(text="💰 Ví của tôi")
        ],
        [
            KeyboardButton(text="🧾 Lịch sử đơn hàng"),
            KeyboardButton(text="🎁 Khuyến mãi")
        ],
        [
            KeyboardButton(text="👤 Tài khoản"),
            KeyboardButton(text="💬 Hỗ trợ")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_brand_catalog_keyboard(
    featured_products: Optional[List[dict]] = None
) -> InlineKeyboardMarkup:
    """
    Renders the exact Canboso catalog layout (Image 3):
    - 3-column grid of all 62 Brand buttons
    - Below grid: Featured / hot products (1 per row)
    - Bottom button: 🔄 Cập nhật sản phẩm
    """
    keyboard = []

    # 1. 3-column grid of all 62 brands
    row = []
    for name, slug, icon, _, _ in BRANDS_LAYOUT:
        btn_text = f"{icon} {name}"
        row.append(InlineKeyboardButton(text=btn_text, callback_data=f"b:{slug}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    # 2. Featured / Hot products below brand grid (1 per row, compact MMO style)
    if featured_products:
        for p in featured_products:
            icon = get_product_icon(p["name"])
            price_str = format_mmo_price(p["calculated_price"])
            stock_qty = p.get("available_qty")
            if stock_qty is None or stock_qty >= 9999:
                stock_str = "📦 ∞"
            elif stock_qty <= 0:
                stock_str = "🔴 Hết"
            else:
                stock_str = f"📦 {stock_qty}"

            name_clean = p["name"]
            # Shorten if too long for a single button
            if len(name_clean) > 60:
                name_clean = name_clean[:57] + "..."

            btn_text = f"{icon} {name_clean} | {price_str} | {stock_str}"
            keyboard.append([
                InlineKeyboardButton(text=btn_text, callback_data=f"prod:{p['product_id']}")
            ])

    # 3. Bottom Action Row: Refresh Store
    keyboard.append([
        InlineKeyboardButton(text="🔄 Cập nhật sản phẩm", callback_data="refresh_store")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_brand_packages_keyboard(
    slug: str,
    products: List[dict],
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Renders the packages inside a specific brand ("ấn vào trong mới ra các gói khác"):
    - 1-column list of all package variants for this brand
    - Pagination row if > 1 page
    - Bottom row: [ 🔙 Quay lại danh mục ] [ 🏠 Trang chủ ]
    """
    keyboard = []

    for p in products:
        icon = get_product_icon(p["name"])
        price_str = format_mmo_price(p["calculated_price"])
        stock_qty = p.get("available_qty")
        if stock_qty is None or stock_qty >= 9999:
            stock_str = "📦 ∞"
        elif stock_qty <= 0:
            stock_str = "🔴 Hết hàng"
        else:
            stock_str = f"📦 {stock_qty}"

        name_clean = p["name"]
        if len(name_clean) > 42:
            name_clean = name_clean[:39] + "..."

        btn_text = f"{icon} {name_clean} | {price_str} | {stock_str}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"prod:{p['product_id']}")
        ])

    # Pagination row
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(text="◀️ Trước", callback_data=f"bp:{slug}:{page - 1}")
            )
        nav_row.append(
            InlineKeyboardButton(text=f"Trang {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(text="Sau ▶️", callback_data=f"bp:{slug}:{page + 1}")
            )
        keyboard.append(nav_row)

    # Return buttons
    keyboard.append([
        InlineKeyboardButton(text="🔙 Quay lại danh mục", callback_data="store_brands"),
        InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_products_pagination_keyboard(
    products: List[dict],
    page: int = 1,
    total_pages: int = 1,
    category: Optional[str] = None
) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        stock_badge = f"{p['available_qty']} còn" if p.get("available_qty") is not None else "Sẵn có"
        price_text = format_mmo_price(p['calculated_price'])
        name_short = p['name'][:30].strip()
        icon = get_product_icon(p['name'])
        btn_text = f"{icon} {name_short} | {price_text} | 📦 {stock_badge}"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"prod:{p['product_id']}")
        ])

    # Pagination row
    if total_pages > 1:
        nav_row = []
        cat_param = f":{category}" if category else ""
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(text="◀️ Trước", callback_data=f"page:{page - 1}{cat_param}")
            )
        nav_row.append(
            InlineKeyboardButton(text=f"Trang {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(text="Sau ▶️", callback_data=f"page:{page + 1}{cat_param}")
            )
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="🔙 Quay lại danh mục", callback_data="store_brands"),
        InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard(
    product_id: str,
    brand_slug: Optional[str] = None,
    is_available: bool = True
) -> InlineKeyboardMarkup:
    buttons = []
    if is_available:
        buttons.append([
            InlineKeyboardButton(text="⚡ MUA NGAY (Giao tức thì)", callback_data=f"buy:{product_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="⚠️ Tạm hết hàng", callback_data="noop")
        ])

    # Back navigation
    nav_row = []
    if brand_slug and brand_slug in BRANDS_DICT:
        brand_name = BRANDS_DICT[brand_slug]["name"]
        nav_row.append(
            InlineKeyboardButton(text=f"🔙 {brand_name}", callback_data=f"b:{brand_slug}")
        )
    else:
        nav_row.append(
            InlineKeyboardButton(text="🔙 Danh mục", callback_data="store_brands")
        )

    nav_row.append(
        InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
    )
    buttons.append(nav_row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_quantity_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 Cái", callback_data=f"qty:{product_id}:1"),
                InlineKeyboardButton(text="2 Cái", callback_data=f"qty:{product_id}:2"),
                InlineKeyboardButton(text="5 Cái", callback_data=f"qty:{product_id}:5"),
                InlineKeyboardButton(text="10 Cái", callback_data=f"qty:{product_id}:10")
            ],
            [
                InlineKeyboardButton(text="❌ Hủy bỏ", callback_data=f"prod:{product_id}")
            ]
        ]
    )


def get_slot_months_keyboard(product_id: str, allowed_months: List[int]) -> InlineKeyboardMarkup:
    rows = []
    current_row = []
    for m in allowed_months:
        current_row.append(InlineKeyboardButton(text=f"⏱️ {m} Tháng", callback_data=f"month:{product_id}:{m}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([InlineKeyboardButton(text="❌ Hủy bỏ", callback_data=f"prod:{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_confirm_purchase_keyboard(product_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ XÁC NHẬN MUA NGAY", callback_data="confirm_buy_yes")
            ],
            [
                InlineKeyboardButton(text="❌ HỦY BỎ GIAO DỊCH", callback_data="confirm_buy_no")
            ]
        ]
    )


def get_deposit_amounts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 20.000 VND", callback_data="dep_amt:20000"),
                InlineKeyboardButton(text="💳 50.000 VND", callback_data="dep_amt:50000")
            ],
            [
                InlineKeyboardButton(text="💳 100.000 VND", callback_data="dep_amt:100000"),
                InlineKeyboardButton(text="💳 200.000 VND", callback_data="dep_amt:200000")
            ],
            [
                InlineKeyboardButton(text="💳 500.000 VND", callback_data="dep_amt:500000"),
                InlineKeyboardButton(text="💎 1.000.000 VND", callback_data="dep_amt:1000000")
            ],
            [
                InlineKeyboardButton(text="✏️ Nhập số tiền tùy ý khác", callback_data="dep_amt:custom")
            ]
        ]
    )


def get_deposit_action_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Tôi đã chuyển tiền (Kiểm tra)", callback_data=f"check_dep:{transaction_id}")
            ],
            [
                InlineKeyboardButton(text="❌ Hủy giao dịch", callback_data="cancel_dep")
            ]
        ]
    )


def get_admin_deposit_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Duyệt nạp tiền", callback_data=f"adm_approve_dep:{transaction_id}"),
                InlineKeyboardButton(text="❌ Từ chối", callback_data=f"adm_reject_dep:{transaction_id}")
            ]
        ]
    )


# Backward compatibility aliases
get_store_catalog_keyboard = get_brand_catalog_keyboard
get_categories_keyboard = get_brand_catalog_keyboard
get_qr_amount_keyboard = get_deposit_amounts_keyboard
get_qr_action_keyboard = get_deposit_action_keyboard
