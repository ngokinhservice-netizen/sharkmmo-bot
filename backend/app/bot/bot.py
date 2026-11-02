import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from backend.app.core.config import settings
from backend.app.bot.middlewares.db import DbSessionMiddleware
from backend.app.bot.middlewares.throttling import ThrottlingMiddleware
from backend.app.bot.middlewares.auth import UserAuthMiddleware

from backend.app.handlers import (
    start,
    catalog,
    search,
    wallet,
    orders,
    promotions,
    account,
    support,
    buy_flow,
    admin_bot
)

logger = logging.getLogger("sharkmmo.bot")


def create_bot() -> Bot:
    if not settings.BOT_TOKEN:
        logger.warning("BOT_TOKEN is not configured in environment!")
    return Bot(
        token=settings.BOT_TOKEN or "123456:dummy_token_sharkmmo",
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Register Middlewares (Order matters: DB -> Throttling -> Auth)
    dp.update.middleware(DbSessionMiddleware())
    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())
    dp.update.middleware(UserAuthMiddleware())

    # Register Handler Routers
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(search.router)
    dp.include_router(wallet.router)
    dp.include_router(orders.router)
    dp.include_router(promotions.router)
    dp.include_router(account.router)
    dp.include_router(support.router)
    dp.include_router(buy_flow.router)
    dp.include_router(admin_bot.router)

    return dp
