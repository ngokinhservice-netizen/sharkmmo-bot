import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.models.models import Base, User, ProductCache, Order
from backend.app.services.order_service import OrderService
from backend.app.services.canboso import BalanceResponse, PurchaseResponse, PurchaseOrderInfo, PurchasePaymentInfo, PurchaseOrderDelivery, PurchaseOrderDeliveryAccount


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
async def test_order_insufficient_balance(async_db):
    user = User(
        telegram_id=123456,
        username="buyer_test",
        balance=10000.0,
        total_spent=0.0
    )
    product = ProductCache(
        product_id="prod_chatgpt",
        name="ChatGPT Plus",
        product_type="account",
        source_price=50000.0,
        calculated_price=60000.0,
        is_active=True
    )
    async_db.add_all([user, product])
    await async_db.commit()

    res = await OrderService.create_purchase_order(
        session=async_db,
        telegram_id=123456,
        product_id="prod_chatgpt",
        quantity=1
    )

    assert res["success"] is False
    assert res["need_deposit"] is True
    assert res["missing_amount"] == 50000.0  # 60,000 - 10,000 = 50,000


@pytest.mark.asyncio
async def test_order_purchase_success(async_db):
    user = User(
        telegram_id=999888,
        username="whale_buyer",
        balance=200000.0,
        total_spent=0.0
    )
    product = ProductCache(
        product_id="prod_chatgpt_vip",
        name="ChatGPT Plus VIP",
        product_type="account",
        source_price=50000.0,
        custom_price=65000.0,
        calculated_price=65000.0,
        is_active=True
    )
    async_db.add_all([user, product])
    await async_db.commit()

    mock_balance = BalanceResponse(
        success=True,
        balance=500000.0,
        balanceVnd=500000.0
    )

    mock_purchase = PurchaseResponse(
        success=True,
        order=PurchaseOrderInfo(
            orderCode="CANBOSO_ORDER_12345",
            status="completed",
            productName="ChatGPT Plus VIP",
            productType="account",
            quantity=1
        ),
        payment=PurchasePaymentInfo(
            amount=50000.0,
            currency="VND",
            balance=450000.0
        ),
        delivery=PurchaseOrderDelivery(
            accounts=[
                PurchaseOrderDeliveryAccount(
                    user="test_acc@gmail.com",
                    password="secret_pass_123"
                )
            ]
        )
    )

    with patch("backend.app.services.canboso.canboso_client.get_balance", new_callable=AsyncMock) as mock_get_bal, \
         patch("backend.app.services.canboso.canboso_client.purchase", new_callable=AsyncMock) as mock_purch:

        mock_get_bal.return_value = mock_balance
        mock_purch.return_value = mock_purchase

        res = await OrderService.create_purchase_order(
            session=async_db,
            telegram_id=999888,
            product_id="prod_chatgpt_vip",
            quantity=1
        )

        assert res["success"] is True
        assert res["canboso_order_code"] == "CANBOSO_ORDER_12345"
        assert res["user_balance"] == 135000.0  # 200,000 - 65,000 = 135,000
        assert len(res["delivery_data"]) == 1
        assert res["delivery_data"][0]["user"] == "test_acc@gmail.com"
