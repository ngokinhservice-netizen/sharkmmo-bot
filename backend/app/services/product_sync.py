import datetime
import logging
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ProductCache, utcnow
from backend.app.services.canboso import canboso_client, ProductsResponse
from backend.app.services.pricing import pricing_engine
from backend.app.services.brand_catalog import match_product_to_brand

logger = logging.getLogger("sharkmmo.sync")


def categorize_product(name: str, product_type: str) -> str:
    lower = name.lower()
    if any(k in lower for k in ["chatgpt", "gpt", "openai", "claude", "gemini", "midjourney", "canva", "adobe", "capcut"]):
        return "🤖 AI & Đồ họa"
    elif any(k in lower for k in ["facebook", "fb", "tiktok", "instagram", "threads", "twitter", "x.com", "tele", "telegram"]):
        return "📱 Mạng xã hội"
    elif any(k in lower for k in ["proxy", "vpn", "vps", "nordvpn", "surfshark", "expressvpn", "ip"]):
        return "🛡️ Proxy & VPN"
    elif any(k in lower for k in ["netflix", "spotify", "youtube", "zoom", "google drive", "onedrive", "office"]):
        return "🎬 Giải trí & Phần mềm"
    elif any(k in lower for k in ["steam", "game", "riot", "roblox", "valorant", "discord"]):
        return "🎮 Game & Discord"
    return "⚡ Sản phẩm số MMO"


async def sync_canboso_products(session: AsyncSession, force_refresh: bool = True) -> Dict[str, Any]:
    """
    Sync products from Canboso API and recalculate selling prices.
    Preserves admin custom pricing rules and custom markup overrides.
    """
    try:
        response: ProductsResponse = await canboso_client.get_products(force_refresh=force_refresh)
    except Exception as e:
        logger.error(f"Failed to fetch products from Canboso: {e}")
        raise

    added_count = 0
    updated_count = 0
    now = utcnow()

    for item in response.products:
        query = select(ProductCache).where(ProductCache.product_id == item.productId)
        res = await session.execute(query)
        db_product = res.scalars().first()

        source_price = item.price.amount
        currency = item.price.currency or "VND"
        available_qty = item.availability.available if item.availability else 0
        sold_qty = item.availability.sold if item.availability else 0
        promotions = [p.model_dump() for p in item.promotions] if item.promotions else []
        reqs = item.purchaseRequirements.model_dump() if item.purchaseRequirements else None

        brand_slug = match_product_to_brand(item.name, item.emoji)

        if db_product:
            # Update existing
            db_product.name = item.name
            db_product.description = item.description
            db_product.image = item.image
            db_product.emoji = item.emoji
            db_product.brand_slug = brand_slug
            db_product.product_type = item.productType
            db_product.source_price = source_price
            db_product.currency = currency
            db_product.available_qty = available_qty
            db_product.sold_qty = sold_qty
            db_product.promotions = promotions
            db_product.purchase_requirements = reqs
            db_product.last_synced_at = now
            db_product.is_active = True

            # Recalculate price
            calc_price, _ = await pricing_engine.calculate_product_price(session, db_product)
            db_product.calculated_price = calc_price
            updated_count += 1
        else:
            # Create new
            category = categorize_product(item.name, item.productType)
            db_product = ProductCache(
                product_id=item.productId,
                name=item.name,
                description=item.description,
                image=item.image,
                emoji=item.emoji,
                brand_slug=brand_slug,
                product_type=item.productType,
                category=category,
                source_price=source_price,
                currency=currency,
                available_qty=available_qty,
                sold_qty=sold_qty,
                promotions=promotions,
                purchase_requirements=reqs,
                is_active=True,
                last_synced_at=now
            )
            session.add(db_product)
            await session.flush()  # Flush to generate ID

            # Calculate price
            calc_price, _ = await pricing_engine.calculate_product_price(session, db_product)
            db_product.calculated_price = calc_price
            added_count += 1

    # Deactivate products not in current shop API
    synced_product_ids = [item.productId for item in response.products]
    if synced_product_ids:
        from sqlalchemy import update
        deact_stmt = (
            update(ProductCache)
            .where(ProductCache.product_id.not_in(synced_product_ids))
            .values(is_active=False)
        )
        await session.execute(deact_stmt)

    await session.commit()
    logger.info(f"Sync complete: {added_count} added, {updated_count} updated, {len(synced_product_ids)} active.")
    return {
        "success": True,
        "total": len(response.products),
        "added": added_count,
        "updated": updated_count
    }
