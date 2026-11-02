from fastapi import APIRouter
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.products import router as products_router
from backend.app.api.v1.pricing import router as pricing_router
from backend.app.api.v1.orders import router as orders_router
from backend.app.api.v1.users import router as users_router
from backend.app.api.v1.payments import router as payments_router
from backend.app.api.v1.webhooks import router as webhooks_router
from backend.app.api.v1.settings_api import router as settings_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(dashboard_router)
api_router.include_router(products_router)
api_router.include_router(pricing_router)
api_router.include_router(orders_router)
api_router.include_router(users_router)
api_router.include_router(payments_router)
api_router.include_router(webhooks_router)
api_router.include_router(settings_router)
