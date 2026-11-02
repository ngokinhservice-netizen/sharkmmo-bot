import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.models.models import Base, ProductCache, PricingRule
from backend.app.services.pricing import PricingEngine


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_global_pricing_rule(async_db):
    rule = PricingRule(
        rule_type="global",
        target_name="ALL",
        markup_type="percent",
        markup_value=25.0,  # +25%
        round_to=1000,
        priority=1,
        is_active=True
    )
    async_db.add(rule)
    await async_db.commit()

    product = ProductCache(
        product_id="prod_test_1",
        name="ChatGPT Plus 1 Month",
        product_type="account",
        category="🤖 AI & Đồ họa",
        source_price=100000.0,
        currency="VND",
        calculated_price=0.0
    )
    async_db.add(product)
    await async_db.commit()

    price, meta = await PricingEngine.calculate_product_price(async_db, product)
    # 100,000 * 1.25 = 125,000
    assert price == 125000.0
    assert meta["rule_type"] == "global"
    assert meta["profit"] == 25000.0


@pytest.mark.asyncio
async def test_category_pricing_override(async_db):
    global_rule = PricingRule(
        rule_type="global",
        target_name="ALL",
        markup_type="percent",
        markup_value=10.0,
        priority=1,
        is_active=True
    )
    cat_rule = PricingRule(
        rule_type="category",
        target_name="🛡️ Proxy & VPN",
        markup_type="fixed",
        markup_value=15000.0,  # Fixed +15,000đ
        priority=2,
        is_active=True
    )
    async_db.add_all([global_rule, cat_rule])
    await async_db.commit()

    product = ProductCache(
        product_id="proxy_v4",
        name="Proxy IPv4 Viettel",
        product_type="account",
        category="🛡️ Proxy & VPN",
        source_price=30000.0,
        currency="VND",
        calculated_price=0.0
    )
    async_db.add(product)
    await async_db.commit()

    price, meta = await PricingEngine.calculate_product_price(async_db, product)
    # Category rule has higher priority: 30,000 + 15,000 = 45,000
    assert price == 45000.0
    assert meta["rule_type"] == "category"
    assert meta["profit"] == 15000.0


@pytest.mark.asyncio
async def test_product_direct_override(async_db):
    product = ProductCache(
        product_id="netflix_vip",
        name="Netflix 4K UHD",
        product_type="account",
        category="🎬 Giải trí & Phần mềm",
        source_price=45000.0,
        custom_price=69000.0,  # Explicit override
        currency="VND",
        calculated_price=0.0
    )
    async_db.add(product)
    await async_db.commit()

    price, meta = await PricingEngine.calculate_product_price(async_db, product)
    assert price == 69000.0
    assert meta["rule_type"] == "product_override"
    assert meta["profit"] == 24000.0


def test_rounding_mechanism():
    # 52,340 rounded to 1,000 -> 53,000
    assert PricingEngine.apply_rounding(52340, 1000) == 53000
    # 50,000 rounded to 1,000 -> 50,000
    assert PricingEngine.apply_rounding(50000, 1000) == 50000
    # 50,001 rounded to 1,000 -> 51,000
    assert PricingEngine.apply_rounding(50001, 1000) == 51000
