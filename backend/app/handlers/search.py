from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache
from backend.app.keyboards.menus import get_products_pagination_keyboard

router = Router(name="search")


class SearchState(StatesGroup):
    waiting_for_keyword = State()


@router.message(F.text == "🔎 Tìm kiếm")
async def start_search(message: Message, state: FSMContext):
    await state.set_state(SearchState.waiting_for_keyword)
    await message.answer(
        "🔎 <b>TÌM KIẾM SẢN PHẨM SHARKMMO</b>\n\n"
        "Vui lòng nhập tên sản phẩm, từ khóa cần tìm (Ví dụ: <i>ChatGPT, Netflix, Proxy, Facebook...</i>):",
        parse_mode="HTML"
    )


@router.message(SearchState.waiting_for_keyword)
async def process_search_keyword(message: Message, state: FSMContext, session: AsyncSession):
    keyword = message.text.strip()
    await state.clear()

    if len(keyword) < 2:
        await message.answer("⚠️ Từ khóa tìm kiếm quá ngắn (tối thiểu 2 ký tự). Vui lòng thử lại!")
        return

    pattern = f"%{keyword}%"
    q = (
        select(ProductCache)
        .where(
            ProductCache.is_active == True,
            or_(
                ProductCache.name.ilike(pattern),
                ProductCache.description.ilike(pattern),
                ProductCache.category.ilike(pattern)
            )
        )
        .limit(15)
    )

    res = await session.execute(q)
    products = res.scalars().all()

    if not products:
        await message.answer(
            f"❌ Không tìm thấy sản phẩm nào khớp với từ khóa: <b>{keyword}</b>\n"
            f"👉 Thử dùng từ khóa ngắn hơn hoặc xem theo <b>📦 Danh mục sản phẩm</b>.",
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

    await message.answer(
        f"🔍 Tìm thấy <b>{len(products)}</b> sản phẩm phù hợp với từ khóa: <b>{keyword}</b>\n\n"
        f"<i>Nhấn vào sản phẩm để xem chi tiết:</i>",
        reply_markup=get_products_pagination_keyboard(prod_dicts, page=1, total_pages=1),
        parse_mode="HTML"
    )
