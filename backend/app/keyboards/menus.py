from typing import List, Optional
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def get_main_menu() -> ReplyKeyboardMarkup:
    """
    Standard Vietnamese 8-button menu with modern styling:
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


def get_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    buttons = []
    # 2 columns per row for a clean modern app grid
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
        price_text = f"{p['calculated_price']:,.0f}đ"
        name_short = p['name'][:22].strip()
        btn_text = f"🔹 {name_short} | {price_text} ({stock_badge})"
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
        InlineKeyboardButton(text="🔙 Danh sách sản phẩm", callback_data="products:page:1"),
        InlineKeyboardButton(text="📂 Danh mục", callback_data="categories")
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
