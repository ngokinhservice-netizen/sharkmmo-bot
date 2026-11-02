import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.models.models import Base, User, PaymentTransaction
from backend.app.payments.vietqr import get_vietqr_url
from backend.app.payments.payment_service import payment_service
from backend.app.payments.sepay import sepay_processor


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_maker() as session:
        yield session

    await engine.dispose()


def test_vietqr_url_generation():
    url = get_vietqr_url(
        amount=50000,
        transfer_content="SHARK NAP 123456",
        bank_code="MB",
        account_no="0988888888",
        account_name="SHARKMMO STORE"
    )
    assert "https://img.vietqr.io/image/MB-0988888888-compact2.png" in url
    assert "amount=50000" in url
    assert "SHARK" in url


@pytest.mark.asyncio
async def test_deposit_and_manual_confirmation(async_db):
    user = User(
        telegram_id=555666,
        username="deposit_tester",
        balance=0.0
    )
    async_db.add(user)
    await async_db.commit()

    # Create deposit
    dep = await payment_service.create_deposit_request(async_db, telegram_id=555666, amount=100000.0)
    assert dep["success"] is True
    tx_id = dep["transaction_id"]

    # Confirm deposit
    conf = await payment_service.confirm_payment(async_db, transaction_id=tx_id, confirmed_by="admin_test")
    assert conf["success"] is True
    assert conf["new_balance"] == 100000.0

    # Idempotent second confirmation
    conf2 = await payment_service.confirm_payment(async_db, transaction_id=tx_id)
    assert conf2["already_completed"] is True


@pytest.mark.asyncio
async def test_sepay_webhook_auto_match(async_db):
    user = User(
        telegram_id=777888,
        username="sepay_tester",
        balance=20000.0
    )
    async_db.add(user)
    await async_db.commit()

    # User creates deposit
    dep = await payment_service.create_deposit_request(async_db, telegram_id=777888, amount=50000.0)
    content = dep["transfer_content"]

    # Simulate SePay webhook incoming
    webhook_payload = {
        "id": 9991234,
        "gateway": "MBBank",
        "accountNumber": "0988888888",
        "amountIn": 50000.0,
        "transactionContent": f"MBVCB.VN12345. {content} REF123",
        "referenceNumber": "FT26999"
    }

    res = await sepay_processor.process_webhook(async_db, webhook_payload)
    assert res["success"] is True
    assert res["amount"] == 50000.0
    assert res["new_balance"] == 70000.0  # 20,000 + 50,000

    # Simulate duplicate webhook replay
    res_dup = await sepay_processor.process_webhook(async_db, webhook_payload)
    assert res_dup["already_processed"] is True
