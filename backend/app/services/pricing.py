import math
import logging
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import PricingRule, ProductCache
from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.pricing")


class PricingEngine:
    """
    Calculates final selling price based on hierarchical rules:
    Priority 1: Product-specific custom price or markup
    Priority 2: Category-specific markup rule
    Priority 3: Global markup rule
    Priority 4: Default system settings
    """

    @staticmethod
    def apply_rounding(price: float, round_to: int = 1000) -> float:
        if round_to <= 1:
            return round(price)
        return math.ceil(price / round_to) * round_to

    @classmethod
    async def calculate_product_price(
        cls,
        session: AsyncSession,
        product: ProductCache
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate final price for a product.
        Returns (final_price, rule_metadata)
        """
        source_price = product.source_price

        # Check Priority 1: Product direct override price
        if product.custom_price is not None and product.custom_price > 0:
            return product.custom_price, {
                "rule_type": "product_override",
                "applied_value": product.custom_price,
                "source_price": source_price,
                "profit": product.custom_price - source_price
            }

        # Check Priority 1.1: Product specific custom markup
        if product.custom_markup_type and product.custom_markup_value is not None:
            markup_type = product.custom_markup_type
            markup_val = product.custom_markup_value
            if markup_type == "percent":
                calc = source_price * (1.0 + (markup_val / 100.0))
            else:
                calc = source_price + markup_val
            rounded = cls.apply_rounding(calc, settings.DEFAULT_ROUND_TO)
            return rounded, {
                "rule_type": "product_markup",
                "markup_type": markup_type,
                "markup_value": markup_val,
                "source_price": source_price,
                "profit": rounded - source_price
            }

        # Check Priority 2: Category specific rule
        query_cat = (
            select(PricingRule)
            .where(
                PricingRule.rule_type == "category",
                PricingRule.target_name == product.category,
                PricingRule.is_active == True
            )
            .order_by(PricingRule.priority.desc())
        )
        res_cat = await session.execute(query_cat)
        cat_rule = res_cat.scalars().first()

        if cat_rule:
            return cls._apply_rule(cat_rule, source_price)

        # Check Priority 3: Global rule
        query_global = (
            select(PricingRule)
            .where(
                PricingRule.rule_type == "global",
                PricingRule.is_active == True
            )
            .order_by(PricingRule.priority.desc())
        )
        res_global = await session.execute(query_global)
        global_rule = res_global.scalars().first()

        if global_rule:
            return cls._apply_rule(global_rule, source_price)

        # Fallback Priority 4: Default Settings
        markup_type = settings.DEFAULT_MARKUP_TYPE
        markup_val = settings.DEFAULT_MARKUP_VALUE
        round_to = settings.DEFAULT_ROUND_TO

        if markup_type == "percent":
            calc = source_price * (1.0 + (markup_val / 100.0))
        else:
            calc = source_price + markup_val

        final_price = cls.apply_rounding(calc, round_to)
        return final_price, {
            "rule_type": "default_setting",
            "markup_type": markup_type,
            "markup_value": markup_val,
            "round_to": round_to,
            "source_price": source_price,
            "profit": final_price - source_price
        }

    @classmethod
    def _apply_rule(cls, rule: PricingRule, source_price: float) -> Tuple[float, Dict[str, Any]]:
        if rule.markup_type == "percent":
            calc = source_price * (1.0 + (rule.markup_value / 100.0))
        else:
            calc = source_price + rule.markup_value

        # Apply min/max price constraint
        if rule.min_price is not None and calc < rule.min_price:
            calc = rule.min_price
        if rule.max_price is not None and calc > rule.max_price:
            calc = rule.max_price

        # Apply rounding
        final_price = cls.apply_rounding(calc, rule.round_to)

        return final_price, {
            "rule_id": rule.id,
            "rule_type": rule.rule_type,
            "target": rule.target_name,
            "markup_type": rule.markup_type,
            "markup_value": rule.markup_value,
            "round_to": rule.round_to,
            "source_price": source_price,
            "profit": final_price - source_price
        }


pricing_engine = PricingEngine()
