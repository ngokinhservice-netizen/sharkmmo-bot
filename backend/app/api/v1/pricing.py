from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import PricingRule, ProductCache, utcnow
from backend.app.services.pricing import pricing_engine

router = APIRouter(prefix="/pricing", tags=["Pricing"])


class PricingRuleCreateSchema(BaseModel):
    rule_type: str  # "global", "category", "product"
    target_name: str  # "ALL", category name, or product_id
    markup_type: str = "percent"  # "percent", "fixed"
    markup_value: float = 20.0
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    round_to: int = 1000
    priority: int = 0
    is_active: bool = True


class PricingRuleUpdateSchema(BaseModel):
    rule_type: Optional[str] = None
    target_name: Optional[str] = None
    markup_type: Optional[str] = None
    markup_value: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    round_to: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/rules", dependencies=[Depends(verify_admin_key)])
async def list_pricing_rules(session: AsyncSession = Depends(get_db_session)):
    q = select(PricingRule).order_by(PricingRule.priority.desc(), PricingRule.id.asc())
    res = await session.execute(q)
    rules = res.scalars().all()
    return {"success": True, "rules": rules}


@router.post("/rules", dependencies=[Depends(verify_admin_key)])
async def create_pricing_rule(
    payload: PricingRuleCreateSchema,
    session: AsyncSession = Depends(get_db_session)
):
    rule = PricingRule(
        rule_type=payload.rule_type,
        target_name=payload.target_name,
        markup_type=payload.markup_type,
        markup_value=payload.markup_value,
        min_price=payload.min_price,
        max_price=payload.max_price,
        round_to=payload.round_to,
        priority=payload.priority,
        is_active=payload.is_active,
        created_at=utcnow(),
        updated_at=utcnow()
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)

    # Re-apply pricing to all products
    await apply_pricing_to_all(session)

    return {"success": True, "rule": rule}


@router.put("/rules/{id}", dependencies=[Depends(verify_admin_key)])
async def update_pricing_rule(
    id: int,
    payload: PricingRuleUpdateSchema,
    session: AsyncSession = Depends(get_db_session)
):
    q = select(PricingRule).where(PricingRule.id == id)
    res = await session.execute(q)
    rule = res.scalars().first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, val)

    rule.updated_at = utcnow()
    await session.commit()
    await session.refresh(rule)

    # Re-apply pricing to all products
    await apply_pricing_to_all(session)

    return {"success": True, "rule": rule}


@router.delete("/rules/{id}", dependencies=[Depends(verify_admin_key)])
async def delete_pricing_rule(id: int, session: AsyncSession = Depends(get_db_session)):
    q = select(PricingRule).where(PricingRule.id == id)
    res = await session.execute(q)
    rule = res.scalars().first()

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await session.delete(rule)
    await session.commit()

    # Re-apply pricing to all products
    await apply_pricing_to_all(session)

    return {"success": True, "message": "Rule deleted"}


@router.post("/apply-all", dependencies=[Depends(verify_admin_key)])
async def reapply_all_pricing(session: AsyncSession = Depends(get_db_session)):
    count = await apply_pricing_to_all(session)
    return {"success": True, "updated_products": count}


async def apply_pricing_to_all(session: AsyncSession) -> int:
    q = select(ProductCache)
    res = await session.execute(q)
    products = res.scalars().all()

    for p in products:
        calc_price, _ = await pricing_engine.calculate_product_price(session, p)
        p.calculated_price = calc_price

    await session.commit()
    return len(products)
