import time
import uuid
import logging
from typing import Optional, Dict, Any, List
import httpx
from pydantic import BaseModel, Field

from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.canboso")


# --- Custom Exceptions ---
class CanbosoAPIError(Exception):
    """Base exception for Canboso API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data or {}


class CanbosoAuthError(CanbosoAPIError):
    """Raised when authentication fails (HTTP 401)."""
    pass


class CanbosoRateLimitError(CanbosoAPIError):
    """Raised when rate limit is exceeded (HTTP 429)."""
    def __init__(self, message: str, retry_after: int = 12, data: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=429, data=data)
        self.retry_after = retry_after


class CanbosoBadRequestError(CanbosoAPIError):
    """Raised when request payload is invalid (HTTP 400)."""
    pass


class CanbosoOrderNotFoundError(CanbosoAPIError):
    """Raised when an order is not found (HTTP 404)."""
    pass


# --- Pydantic Data Models ---
class ProductPrice(BaseModel):
    amount: float
    currency: str = "VND"
    text: Optional[str] = None


class ProductAvailability(BaseModel):
    available: Optional[int] = 0
    sold: Optional[int] = 0


class ProductPromotion(BaseModel):
    type: Optional[str] = None
    minQty: Optional[float] = None
    percent: Optional[float] = None
    bonusQty: Optional[float] = None


class PurchaseRequirements(BaseModel):
    customerEmail: Optional[bool] = False
    customerAccounts: Optional[bool] = False
    slotMonths: Optional[bool] = False
    quantityFixed: Optional[int] = None
    allowedMonths: Optional[List[int]] = None


class ProductItem(BaseModel):
    productId: str
    name: str
    description: Optional[str] = None
    image: Optional[str] = None
    emoji: Optional[str] = None
    productType: str  # account, slot, upgrade_account
    price: ProductPrice
    availability: Optional[ProductAvailability] = None
    promotions: Optional[List[ProductPromotion]] = []
    purchaseRequirements: Optional[PurchaseRequirements] = None


class ProductsResponse(BaseModel):
    success: bool
    lang: Optional[str] = "vi"
    walletCurrency: Optional[str] = "VND"
    products: List[ProductItem] = []


class BalanceResponse(BaseModel):
    success: bool
    lang: Optional[str] = "vi"
    botSource: Optional[str] = None
    walletCurrency: Optional[str] = "VND"
    balance: float
    balanceVnd: Optional[float] = None
    balanceUsd: Optional[float] = None
    balanceText: Optional[str] = None
    usdtBalance: Optional[float] = 0.0
    usdRate: Optional[float] = None
    updatedAt: Optional[str] = None


class PurchaseOrderDeliveryAccount(BaseModel):
    user: Optional[str] = None
    password: Optional[str] = None
    verifyEmail: Optional[str] = None
    expiryText: Optional[str] = None
    otherInfo: Optional[str] = None


class PurchaseOrderDelivery(BaseModel):
    accounts: Optional[List[PurchaseOrderDeliveryAccount]] = []


class PurchaseOrderInfo(BaseModel):
    orderCode: str
    status: str
    productId: Optional[str] = None
    productName: str
    productType: str
    quantity: int
    bonusQuantity: Optional[int] = 0
    finalQuantity: Optional[int] = None
    slotMonths: Optional[int] = None
    customerEmail: Optional[str] = None
    fulfillmentStatus: Optional[str] = None
    autoCompleted: Optional[bool] = False


class PurchasePaymentInfo(BaseModel):
    amount: float
    amountText: Optional[str] = None
    originalAmount: Optional[float] = None
    originalAmountText: Optional[str] = None
    discountPercent: Optional[float] = 0.0
    discountAmount: Optional[float] = 0.0
    discountAmountText: Optional[str] = None
    currency: str = "VND"
    balance: float
    balanceText: Optional[str] = None


class PurchaseResponse(BaseModel):
    success: bool
    lang: Optional[str] = "vi"
    order: PurchaseOrderInfo
    payment: PurchasePaymentInfo
    delivery: Optional[PurchaseOrderDelivery] = None


# --- Cache Helper ---
class MemoryCache:
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}

    def get(self, key: str, ttl_seconds: int) -> Optional[Any]:
        if key in self._data:
            if time.time() - self._timestamps[key] < ttl_seconds:
                return self._data[key]
            else:
                del self._data[key]
                del self._timestamps[key]
        return None

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._timestamps[key] = time.time()

    def invalidate(self, key: Optional[str] = None):
        if key:
            self._data.pop(key, None)
            self._timestamps.pop(key, None)
        else:
            self._data.clear()
            self._timestamps.clear()


# Global in-memory cache instance
_cache = MemoryCache()


# --- Canboso Client ---
class CanbosoClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.api_key = api_key or settings.CANBOSO_API_KEY
        self.base_url = (base_url or settings.CANBOSO_BASE_URL).rstrip("/")
        self.timeout = timeout or settings.CANBOSO_TIMEOUT_SECONDS

    def _get_headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": "SHARKMMO-Bot/2.0",
            "Accept": "application/json",
            "x-buyer-key": self.api_key,
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _check_api_key(self):
        if not self.api_key:
            raise CanbosoAuthError("CANBOSO_API_KEY is not configured. Please set CANBOSO_API_KEY in .env file.")

    async def _handle_response_error(self, response: httpx.Response):
        status = response.status_code
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        message = body.get("message") or f"Canboso API error (HTTP {status})"

        if status == 401:
            raise CanbosoAuthError(f"Authentication failed: {message}", status_code=status, data=body)
        elif status == 429:
            retry_after = 12
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except Exception:
                    pass
            elif "rateLimit" in body and isinstance(body["rateLimit"], dict):
                retry_after = body["rateLimit"].get("retryAfter", 12)
            raise CanbosoRateLimitError(
                f"Rate limit exceeded on Canboso API. Retry after {retry_after}s.",
                retry_after=retry_after,
                data=body
            )
        elif status == 400:
            raise CanbosoBadRequestError(f"Bad request: {message}", status_code=status, data=body)
        elif status == 404:
            raise CanbosoOrderNotFoundError(f"Resource not found: {message}", status_code=status, data=body)
        else:
            raise CanbosoAPIError(f"Canboso API HTTP {status}: {message}", status_code=status, data=body)

    async def get_products(self, force_refresh: bool = False) -> ProductsResponse:
        """
        Fetch products from GET /api/v2/telegram-buyer/products
        Uses caching to comply with the 30 req/min rate limit.
        """
        self._check_api_key()
        cache_key = f"products:{self.api_key[:8]}"
        if not force_refresh:
            cached = _cache.get(cache_key, settings.CANBOSO_CACHE_TTL_SECONDS)
            if cached:
                return cached

        url = f"{self.base_url}/api/v2/telegram-buyer/products"
        params = {"key": self.api_key}
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    await self._handle_response_error(resp)

                data = resp.json()
                result = ProductsResponse.model_validate(data)
                _cache.set(cache_key, result)
                return result
            except httpx.RequestError as e:
                logger.error(f"Network error while connecting to Canboso products API: {e}")
                raise CanbosoAPIError(f"Network connection failed: {str(e)}")

    async def get_balance(self, force_refresh: bool = False) -> BalanceResponse:
        """
        Fetch wallet balance from GET /api/v2/telegram-buyer/balance
        """
        self._check_api_key()
        cache_key = f"balance:{self.api_key[:8]}"
        if not force_refresh:
            cached = _cache.get(cache_key, settings.CANBOSO_CACHE_TTL_SECONDS)
            if cached:
                return cached

        url = f"{self.base_url}/api/v2/telegram-buyer/balance"
        params = {"key": self.api_key}
        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    await self._handle_response_error(resp)

                data = resp.json()
                result = BalanceResponse.model_validate(data)
                _cache.set(cache_key, result)
                return result
            except httpx.RequestError as e:
                logger.error(f"Network error while connecting to Canboso balance API: {e}")
                raise CanbosoAPIError(f"Network connection failed: {str(e)}")

    async def purchase(
        self,
        product_id: str,
        quantity: int = 1,
        customer_email: Optional[str] = None,
        customer_accounts: Optional[List[str]] = None,
        slot_months: Optional[int] = None,
        idempotency_key: Optional[str] = None
    ) -> PurchaseResponse:
        """
        Purchase product via POST /api/v2/telegram-buyer/purchase
        Requires Idempotency-Key header.
        Never retries blindly.
        """
        self._check_api_key()
        if not idempotency_key:
            idempotency_key = f"shark-{int(time.time())}-{uuid.uuid4().hex[:12]}"

        url = f"{self.base_url}/api/v2/telegram-buyer/purchase"
        payload: Dict[str, Any] = {
            "key": self.api_key,
            "product_id": product_id,
            "quantity": quantity
        }

        if customer_email:
            payload["customer_email"] = customer_email
        if customer_accounts:
            payload["customer_accounts"] = customer_accounts
        if slot_months is not None:
            payload["slot_months"] = slot_months

        headers = self._get_headers(idempotency_key=idempotency_key)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"Submitting purchase to Canboso: product_id={product_id}, qty={quantity}, idem={idempotency_key}")
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    await self._handle_response_error(resp)

                data = resp.json()
                result = PurchaseResponse.model_validate(data)
                # Invalidate balance cache after successful purchase
                _cache.invalidate(f"balance:{self.api_key[:8]}")
                return result
            except httpx.RequestError as e:
                logger.error(f"Network error while calling Canboso purchase endpoint: {e}")
                raise CanbosoAPIError(f"Network error during purchase: {str(e)}")

    async def get_order_history(self, order_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch order history via GET /api/v2/telegram-buyer/orders
        """
        self._check_api_key()
        url = f"{self.base_url}/api/v2/telegram-buyer/orders"
        params: Dict[str, Any] = {"key": self.api_key}
        if order_code:
            params["orderCode"] = order_code.strip()

        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code != 200:
                    await self._handle_response_error(resp)

                data = resp.json()
                return data.get("orders", [])
            except httpx.RequestError as e:
                logger.error(f"Network error while getting Canboso order history: {e}")
                raise CanbosoAPIError(f"Network error getting order history: {str(e)}")


canboso_client = CanbosoClient()
