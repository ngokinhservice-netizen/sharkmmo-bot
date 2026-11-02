import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from backend.app.services.canboso import (
    CanbosoClient,
    CanbosoAuthError,
    CanbosoRateLimitError,
    CanbosoBadRequestError,
    ProductsResponse,
    BalanceResponse,
    PurchaseResponse
)


@pytest.fixture
def client():
    return CanbosoClient(api_key="tgb_test_secret_buyer_key", base_url="https://canboso.com")


def test_headers_and_idempotency(client):
    headers = client._get_headers(idempotency_key="idem-12345678")
    assert headers["x-buyer-key"] == "tgb_test_secret_buyer_key"
    assert headers["Idempotency-Key"] == "idem-12345678"
    assert headers["Accept"] == "application/json"


@pytest.mark.asyncio
async def test_get_balance_success(client):
    mock_payload = {
        "success": True,
        "lang": "vi",
        "botSource": "primary",
        "walletCurrency": "VND",
        "balance": 250000,
        "balanceVnd": 250000,
        "balanceText": "VND 250,000",
        "usdtBalance": 10.5
    }

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        balance = await client.get_balance(force_refresh=True)

        assert isinstance(balance, BalanceResponse)
        assert balance.success is True
        assert balance.balance == 250000
        assert balance.balanceVnd == 250000
        assert balance.usdtBalance == 10.5


@pytest.mark.asyncio
async def test_rate_limit_error_retry_after(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 429
    mock_resp.headers = {"Retry-After": "25"}
    mock_resp.json.return_value = {
        "success": False,
        "message": "Too many requests",
        "rateLimit": {"retryAfter": 25}
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(CanbosoRateLimitError) as exc_info:
            await client.get_products(force_refresh=True)

        assert exc_info.value.retry_after == 25
        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_auth_error_handling(client):
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "success": False,
        "message": "Invalid API key"
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(CanbosoAuthError) as exc_info:
            await client.get_products(force_refresh=True)

        assert "Invalid API key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_purchase_success(client):
    mock_purchase_payload = {
        "success": True,
        "lang": "vi",
        "order": {
            "orderCode": "ORDER_CANBOSO_999",
            "status": "completed",
            "productId": "chatgpt_plus",
            "productName": "ChatGPT Plus",
            "productType": "account",
            "quantity": 1,
            "bonusQuantity": 0,
            "finalQuantity": 1
        },
        "payment": {
            "amount": 50000,
            "amountText": "50.000 đ",
            "currency": "VND",
            "balance": 200000
        },
        "delivery": {
            "accounts": [
                {
                    "user": "shark_user@gmail.com",
                    "password": "SuperSecretPassword123",
                    "expiryText": "30 ngày"
                }
            ]
        }
    }

    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_purchase_payload

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await client.purchase(
            product_id="chatgpt_plus",
            quantity=1,
            idempotency_key="idem_test_uuid_999"
        )

        assert isinstance(res, PurchaseResponse)
        assert res.success is True
        assert res.order.orderCode == "ORDER_CANBOSO_999"
        assert len(res.delivery.accounts) == 1
        assert res.delivery.accounts[0].user == "shark_user@gmail.com"
