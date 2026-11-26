import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from backend.app.core.config import settings
from backend.app.bot.middlewares.db import DbSessionMiddleware
from backend.app.bot.middlewares.throttling import ThrottlingMiddleware
from backend.app.bot.middlewares.auth import UserAuthMiddleware
from backend.app.handlers import start

logger = logging.getLogger("sharkmmo.bot")


def create_bot() -> Bot:
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN is not configured in environment!")
    return Bot(
        token=settings.BOT_TOKEN or "8717942584:AAF2XdxB0mf92mjY5GeYOTWstEHU-NuQAm8",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares
    dp.update.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.update.middleware(UserAuthMiddleware())

    # Register only clean notification start router
    dp.include_router(start.router)

    return dp
