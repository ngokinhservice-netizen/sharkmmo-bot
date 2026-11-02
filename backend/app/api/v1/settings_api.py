from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_db_session, verify_admin_key
from backend.app.models.models import Setting, utcnow
from backend.app.core.config import settings

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsUpdateSchema(BaseModel):
    settings: Dict[str, Any]


@router.get("", dependencies=[Depends(verify_admin_key)])
async def get_settings(session: AsyncSession = Depends(get_db_session)):
    q = select(Setting)
    res = await session.execute(q)
    db_settings = res.scalars().all()
    saved_dict = {s.key: s.value for s in db_settings}

    # Mask sensitive items
    bot_token_masked = f"{settings.BOT_TOKEN[:6]}...{settings.BOT_TOKEN[-4:]}" if len(settings.BOT_TOKEN) > 10 else "(Chưa cấu hình)"
    canboso_key_masked = f"{settings.CANBOSO_API_KEY[:6]}...{settings.CANBOSO_API_KEY[-4:]}" if len(settings.CANBOSO_API_KEY) > 10 else "(Chưa cấu hình)"

    return {
        "success": True,
        "config": {
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "bot_token_status": bot_token_masked,
            "canboso_key_status": canboso_key_masked,
            "bank_code": saved_dict.get("bank_code", settings.BANK_CODE),
            "bank_account_no": saved_dict.get("bank_account_no", settings.BANK_ACCOUNT_NO),
            "bank_account_name": saved_dict.get("bank_account_name", settings.BANK_ACCOUNT_NAME),
            "source_balance_alert_threshold": float(saved_dict.get("source_balance_alert_threshold", settings.SOURCE_BALANCE_ALERT_THRESHOLD)),
            "default_markup_type": saved_dict.get("default_markup_type", settings.DEFAULT_MARKUP_TYPE),
            "default_markup_value": float(saved_dict.get("default_markup_value", settings.DEFAULT_MARKUP_VALUE)),
            "default_round_to": int(saved_dict.get("default_round_to", settings.DEFAULT_ROUND_TO)),
            "auto_sync_interval": int(saved_dict.get("auto_sync_interval", settings.AUTO_SYNC_INTERVAL_MINUTES))
        }
    }


@router.post("", dependencies=[Depends(verify_admin_key)])
async def update_settings(payload: SettingsUpdateSchema, session: AsyncSession = Depends(get_db_session)):
    for key, val in payload.settings.items():
        q = select(Setting).where(Setting.key == key)
        res = await session.execute(q)
        s = res.scalars().first()
        val_str = str(val)

        if s:
            s.value = val_str
            s.updated_at = utcnow()
        else:
            s = Setting(
                key=key,
                value=val_str,
                description=f"User configured setting {key}",
                updated_at=utcnow()
            )
            session.add(s)

    await session.commit()
    return {"success": True, "message": "Cài đặt đã được lưu thành công."}
