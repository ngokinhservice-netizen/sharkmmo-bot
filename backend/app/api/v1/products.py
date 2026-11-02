from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import ProductCache, utcnow
from backend.app.services.product_sync import sync_canboso_products
from backend.app.services.pricing import pricing_engine

router = APIRouter(prefix="/products", tags=["Products"])


class ProductUpdateSchema(BaseModel):
    is_active: Optional[bool] = None
    category: Optional[str] = None
    custom_price: Optional[float] = None
    custom_markup_type: Optional[str] = None  # "percent" or "fixed" or ""
    custom_markup_value: Optional[float] = None


@router.get("", dependencies=[Depends(verify_admin_key)])
async def list_products(
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(ProductCache)
    if category:
        q = q.where(ProductCache.category == category)
    if is_active is not None:
        q = q.where(ProductCache.is_active == is_active)
    if search:
        pat = f"%{search}%"
        q = q.where(or_(ProductCache.name.ilike(pat), ProductCache.product_id.ilike(pat)))

    q = q.order_by(ProductCache.id.asc())
    res = await session.execute(q)
    products = res.scalars().all()

    items = []
    for p in products:
        items.append({
            "id": p.id,
            "product_id": p.product_id,
            "name": p.name,
            "description": p.description,
            "category": p.category,
            "product_type": p.product_type,
            "source_price": p.source_price,
            "currency": p.currency,
            "calculated_price": p.calculated_price,
            "custom_price": p.custom_price,
            "custom_markup_type": p.custom_markup_type,
            "custom_markup_value": p.custom_markup_value,
            "profit": p.calculated_price - p.source_price,
            "available_qty": p.available_qty,
            "sold_qty": p.sold_qty,
            "is_active": p.is_active,
            "promotions": p.promotions,
            "purchase_requirements": p.purchase_requirements,
            "last_synced_at": p.last_synced_at.isoformat() if p.last_synced_at else None
        })

    return {"success": True, "count": len(items), "products": items}


@router.post("/sync", dependencies=[Depends(verify_admin_key)])
async def trigger_sync(session: AsyncSession = Depends(get_db_session)):
    try:
        result = await sync_canboso_products(session, force_refresh=True)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.patch("/{id}", dependencies=[Depends(verify_admin_key)])
async def update_product(
    id: int,
    payload: ProductUpdateSchema,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(ProductCache).where(ProductCache.id == id)
    res = await session.execute(q)
    product = res.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.is_active is not None:
        product.is_active = payload.is_active
    if payload.category is not None:
        product.category = payload.category
    if payload.custom_price is not None:
        product.custom_price = payload.custom_price if payload.custom_price > 0 else None
    if payload.custom_markup_type is not None:
        product.custom_markup_type = payload.custom_markup_type if payload.custom_markup_type in ["percent", "fixed"] else None
    if payload.custom_markup_value is not None:
        product.custom_markup_value = payload.custom_markup_value

    product.updated_at = utcnow()

    # Recalculate price
    new_price, _ = await pricing_engine.calculate_product_price(session, product)
    product.calculated_price = new_price

    await session.commit()
    await session.refresh(product)

    return {
        "success": True,
        "product": {
            "id": product.id,
            "product_id": product.product_id,
            "name": product.name,
            "calculated_price": product.calculated_price,
            "custom_price": product.custom_price,
            "custom_markup_type": product.custom_markup_type,
            "custom_markup_value": product.custom_markup_value,
            "is_active": product.is_active
        }
    }
