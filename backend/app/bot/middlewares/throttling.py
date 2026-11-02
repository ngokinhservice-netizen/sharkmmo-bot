import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit_seconds: float = 0.5):
        self.rate_limit = rate_limit_seconds
        self.last_requests: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        tg_user: TgUser = data.get("event_from_user")
        if not tg_user:
            return await handler(event, data)

        now = time.time()
        user_id = tg_user.id

        if user_id in self.last_requests:
            elapsed = now - self.last_requests[user_id]
            if elapsed < self.rate_limit:
                # Throttled
                if isinstance(event, CallbackQuery):
                    await event.answer("⚠️ Thao tác quá nhanh, vui lòng chờ 1 giây!", show_alert=False)
                return None

        self.last_requests[user_id] = now
        return await handler(event, data)
