from typing import List, Optional
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

QUICK_BRAND_TAGS = [
    ("🎨 Canva", "Canva"),
    ("✂️ Capcut", "Capcut"),
    ("🤖 Chat Gpt", "ChatGPT"),
    ("🎬 Youtube", "Youtube"),
    ("💥 Api Claude", "Claude"),
    ("⚙️ Api CodeX", "CodeX"),
    ("✉️ Gmail", "Gmail"),
    ("🎙️ Elevenlabs", "Elevenlabs"),
    ("📁 Notion", "Notion"),
    ("🔑 VPN", "VPN"),
    ("📦 Api Cursor", "Cursor"),
    ("☀️ Suno", "Suno"),
    ("📹 Zoom", "Zoom"),
    ("⚡ Grok Api", "Grok"),
    ("📁 Api Muse", "Muse"),
    ("📁 Api Deepseek", "Deepseek"),
]


def get_product_icon(name: str) -> str:
    n = name.lower()
    if "canva" in n:
        return "🎨"
    if "capcut" in n:
        return "✂️"
    if "chatgpt" in n or "gpt" in n:
        return "🤖"
    if "youtube" in n:
        return "🎬"
    if "claude" in n:
        return "💥"
    if "codex" in n:
        return "⚙️"
    if "gmail" in n:
        return "✉️"
    if "elevenlabs" in n or "eleven" in n:
        return "🎙️"
    if "notion" in n:
        return "📁"
    if "vpn" in n or "hma" in n or "proxy" in n:
        return "🔑"
    if "cursor" in n:
        return "📦"
    if "suno" in n:
        return "☀️"
    if "zoom" in n:
        return "📹"
    if "grok" in n:
        return "⚡"
    if "deepseek" in n:
        return "📁"
    if "gemini" in n:
        return "➕"
    if "netflix" in n:
        return "🍿"
    if "office" in n or "365" in n or "ms365" in n:
        return "🛍️"
    if "duolingo" in n:
        return "🐸"
    if "muse" in n:
        return "🛍️"
    return "🔹"


def format_mmo_price(val: float) -> str:
    if val >= 1_000_000:
        if val % 1_000_000 == 0:
            return f"{int(val // 1_000_000)}Tr"
        return f"{val / 1_000:,.0f}k"
    if val >= 1000:
        if val % 1000 == 0:
            return f"{int(val // 1000)}k"
        return f"{int(val)}"
    return f"{int(val)}đ"


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Standard Vietnamese 8-button menu:
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


def get_store_catalog_keyboard(
    products: List[dict],
    selected_tag: Optional[str] = None,
    page: int = 1,
    total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Layout matching Image 2 exactly:
    - Top: 3-column brand tags grid
    - Middle: Products full-width items with {icon} {name} | {price} | 📦 {stock}
    - Bottom: Refresh & Home / Support controls
    """
    keyboard = []

    # 1. Top Quick Brand Tags in 3 Columns (matching Image 2)
    tag_row = []
    for label, tag_key in QUICK_BRAND_TAGS:
        # Highlight active tag if selected
        btn_text = f"🔥 {label}" if selected_tag == tag_key else label
        tag_row.append(InlineKeyboardButton(text=btn_text, callback_data=f"tag:{tag_key}"))
        if len(tag_row) == 3:
            keyboard.append(tag_row)
            tag_row = []
    if tag_row:
        keyboard.append(tag_row)

    # 2. Product Items (1 per row, clean MMO compact style)
    for p in products:
        icon = get_product_icon(p["name"])
        price_str = format_mmo_price(p["calculated_price"])
        stock_qty = p.get("available_qty") or 0
        stock_str = f"📦 {stock_qty}"

        # Truncate product name smoothly
        name = p["name"].strip()
        if len(name) > 32:
            name = name[:30] + "..."

        btn_text = f"{icon} {name} | {price_str} | {stock_str}"
        keyboard.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"prod:{p['product_id']}")
        ])

    # 3. Pagination row (if multiple pages)
    if total_pages > 1:
        nav_row = []
        tag_param = f":{selected_tag}" if selected_tag else ""
        if page > 1:
            nav_row.append(
                InlineKeyboardButton(text="◀️ Trước", callback_data=f"spage:{page - 1}{tag_param}")
            )
        nav_row.append(
            InlineKeyboardButton(text=f"Trang {page}/{total_pages}", callback_data="noop")
        )
        if page < total_pages:
            nav_row.append(
                InlineKeyboardButton(text="Sau ▶️", callback_data=f"spage:{page + 1}{tag_param}")
            )
        keyboard.append(nav_row)

    # 4. Refresh / All products button
    if selected_tag:
        keyboard.append([
            InlineKeyboardButton(text="🔄 Xem tất cả sản phẩm", callback_data="refresh_store")
        ])
    else:
        keyboard.append([
            InlineKeyboardButton(text="🔄 Làm mới", callback_data="refresh_store")
        ])

    # 5. Bottom Navigation row (matching Image 2)
    keyboard.append([
        InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu"),
        InlineKeyboardButton(text="🧑‍💻 Hỗ trợ", callback_data="support_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(text=f"{cat}", callback_data=f"cat:{cat}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text="🔍 Xem tất cả sản phẩm (Kho hàng)", callback_data="products:page:1")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_products_pagination_keyboard(
    products: List[dict],
    page: int,
    total_pages: int,
    category: Optional[str] = None
) -> InlineKeyboardMarkup:
    buttons = []
    for p in products:
        stock_badge = f"{p['available_qty']} còn" if p.get("available_qty") is not None else "Sẵn có"
        price_text = format_mmo_price(p['calculated_price'])
        name_short = p['name'][:24].strip()
        icon = get_product_icon(p['name'])
        btn_text = f"{icon} {name_short} | {price_text} | 📦 {stock_badge}"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"prod:{p['product_id']}")
        ])

    # Pagination row
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
    if nav_row:
        buttons.append(nav_row)

    # Return button
    buttons.append([
        InlineKeyboardButton(text="📂 Về danh mục chính", callback_data="categories")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_product_detail_keyboard(product_id: str, is_available: bool = True) -> InlineKeyboardMarkup:
    buttons = []
    if is_available:
        buttons.append([
            InlineKeyboardButton(text="⚡ MUA NGAY (Giao tức thì)", callback_data=f"buy:{product_id}")
        ])
    else:
        buttons.append([
            InlineKeyboardButton(text="⚠️ Tạm hết hàng", callback_data="noop")
        ])
    buttons.append([
        InlineKeyboardButton(text="🔄 Cửa hàng", callback_data="refresh_store"),
        InlineKeyboardButton(text="🏠 Trang chủ", callback_data="home_menu")
    ])
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
