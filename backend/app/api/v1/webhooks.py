import logging
from typing import Dict, Any
from fastapi import APIRouter, Header, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session
from backend.app.core.config import settings
from backend.app.payments.sepay import sepay_processor

logger = logging.getLogger("sharkmmo.webhooks")
router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/sepay")
async def handle_sepay_webhook(
    request: Request,
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_db_session)
):
    """
    SePay Webhook endpoint for automated bank transfer notifications.
    """
    if settings.SEPAY_API_KEY:
        # Check authorization token
        # SePay can send `Authorization: Apikey <TOKEN>` or `<TOKEN>`
        expected = settings.SEPAY_API_KEY
        token = authorization.replace("Apikey", "").replace("Bearer", "").strip()
        if token != expected:
            logger.warning(f"Unauthorized SePay webhook call. Header={authorization}")
            raise HTTPException(status_code=401, detail="Invalid webhook authorization token")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON in SePay webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    result = await sepay_processor.process_webhook(session, payload)
    return result


@router.post("/bank")
async def handle_generic_bank_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Generic bank transfer webhook endpoint.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    result = await sepay_processor.process_webhook(session, payload)
    return result
