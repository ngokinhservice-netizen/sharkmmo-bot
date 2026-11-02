import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import User, utcnow
from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.bot.auth")


class UserAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        session: AsyncSession = data.get("session")
        tg_user: TgUser = data.get("event_from_user")

        if not tg_user or not session:
            return await handler(event, data)

        telegram_id = tg_user.id
        is_admin_user = telegram_id in settings.ADMIN_IDS

        # Query existing user
        query = select(User).where(User.telegram_id == telegram_id)
        res = await session.execute(query)
        db_user = res.scalars().first()

        if not db_user:
            # Auto-register new user
            db_user = User(
                telegram_id=telegram_id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                balance=0.0,
                total_spent=0.0,
                total_orders=0,
                is_banned=False,
                role="admin" if is_admin_user else "user",
                created_at=utcnow(),
                updated_at=utcnow()
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            logger.info(f"Registered new Telegram user: {telegram_id} (@{tg_user.username})")
        else:
            # Sync user profile if updated
            changed = False
            if db_user.username != tg_user.username:
                db_user.username = tg_user.username
                changed = True
            if db_user.first_name != tg_user.first_name:
                db_user.first_name = tg_user.first_name
                changed = True
            if is_admin_user and db_user.role != "admin":
                db_user.role = "admin"
                changed = True

            if changed:
                db_user.updated_at = utcnow()
                await session.commit()

        # Check banned status
        if db_user.is_banned:
            msg = "🚫 Tài khoản của bạn đã bị khóa khỏi hệ thống SHARKMMO. Vui lòng liên hệ Admin để được hỗ trợ."
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            return None

        data["current_user"] = db_user
        return await handler(event, data)
