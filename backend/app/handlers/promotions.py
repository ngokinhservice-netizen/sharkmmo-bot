from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache

router = Router(name="promotions")


@router.message(F.text == "🎁 Khuyến mãi")
async def show_promotions(message: Message, session: AsyncSession):
    # Fetch products that have active promotions
    q = select(ProductCache).where(ProductCache.is_active == True)
    res = await session.execute(q)
    products = res.scalars().all()

    promo_list = []
    for p in products:
        if p.promotions:
            for pr in p.promotions:
                min_q = int(pr.get("minQty", 1))
                pct = pr.get("percent", 0)
                bonus = pr.get("bonusQty")
                bonus_str = f" + Tặng {bonus} cái" if bonus else ""
                promo_list.append(
                    f"🔥 <b>{p.name}</b>\n"
                    f"   • Mua từ <b>{min_q}</b> cái: Giảm <b>{pct}%</b>{bonus_str}\n"
                    f"   • Giá gốc: {p.calculated_price:,.0f} VND\n"
                )

    if not promo_list:
        promo_text = (
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
            "   🎁 <b>CHƯƠNG TRÌNH KHUYẾN MÃI</b> 🎁\n"
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
            "Hiện tại chưa có chương trình giảm giá tự động nào đang chạy.\n"
            "Hãy theo dõi kênh thông báo để không bỏ lỡ các đợt Flash Sale nhé!\n\n"
            "📢 <i>Kênh săn deal: @SharkMMO_Channel</i>"
        )
    else:
        promo_text = (
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n"
            "   🎁 <b>ƯU ĐÃI & CHIẾT KHẤU MUA SỈ</b> 🎁\n"
            "🦈 ━━━━━━━━━━━━━━━━━━━━━━ 🦈\n\n"
            + "\n".join(promo_list)
            + "\n💡 <i>Mức chiết khấu sẽ được tự động áp dụng trực tiếp khi bạn chọn số lượng tương ứng!</i>"
        )

    await message.answer(promo_text, parse_mode="HTML")
