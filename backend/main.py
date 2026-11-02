import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.app.core.config import settings
from backend.app.database.session import init_db, AsyncSessionLocal
from backend.app.models.models import PricingRule, ProductCache, utcnow
from backend.app.services.product_sync import sync_canboso_products
from backend.app.api.router import api_router
from backend.app.bot.bot import create_bot, create_dispatcher

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sharkmmo")

bot_task: asyncio.Task = None
scheduler_task: asyncio.Task = None


async def background_sync_worker():
    """Periodically sync products from Canboso in background"""
    logger.info("Background product sync worker started.")
    while True:
        try:
            interval_sec = max(300, settings.AUTO_SYNC_INTERVAL_MINUTES * 60)
            await asyncio.sleep(interval_sec)
            if settings.CANBOSO_API_KEY:
                logger.info("Executing scheduled product sync...")
                async with AsyncSessionLocal() as session:
                    await sync_canboso_products(session, force_refresh=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in background sync worker: {e}")


async def seed_default_data():
    async with AsyncSessionLocal() as session:
        # Seed default global pricing rule if none exists
        q = select(PricingRule).where(PricingRule.rule_type == "global")
        res = await session.execute(q)
        if not res.scalars().first():
            global_rule = PricingRule(
                rule_type="global",
                target_name="ALL",
                markup_type=settings.DEFAULT_MARKUP_TYPE,
                markup_value=settings.DEFAULT_MARKUP_VALUE,
                round_to=settings.DEFAULT_ROUND_TO,
                priority=1,
                is_active=True,
                created_at=utcnow(),
                updated_at=utcnow()
            )
            session.add(global_rule)
            await session.commit()
            logger.info("Seeded default global pricing rule.")

        # If CANBOSO_API_KEY is present and product cache is empty, do an initial sync
        if settings.CANBOSO_API_KEY:
            prod_count = await session.scalar(select(ProductCache.id))
            if not prod_count:
                logger.info("Initiating first-time product sync from Canboso API...")
                try:
                    await sync_canboso_products(session, force_refresh=True)
                except Exception as e:
                    logger.warning(f"Initial Canboso sync skipped or failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task, scheduler_task

    logger.info("🚀 Starting SHARKMMO Backend...")
    # 1. Initialize Database
    await init_db()
    await seed_default_data()

    # 2. Start Background Scheduler Task
    scheduler_task = asyncio.create_task(background_sync_worker())

    # 3. Start Telegram Bot Polling if BOT_TOKEN configured
    if settings.BOT_TOKEN and not settings.BOT_TOKEN.startswith("dummy"):
        logger.info("🤖 Starting Telegram Bot polling...")
        bot = create_bot()
        dp = create_dispatcher()

        async def run_bot_polling():
            try:
                await bot.delete_webhook(drop_pending_updates=True)
                await dp.start_polling(bot)
            except asyncio.CancelledError:
                logger.info("Bot polling task cancelled.")
            except Exception as e:
                logger.error(f"Telegram Bot polling error: {e}")
            finally:
                await bot.session.close()

        bot_task = asyncio.create_task(run_bot_polling())
    else:
        logger.warning("BOT_TOKEN is not set. Telegram Bot polling disabled. Set BOT_TOKEN in .env to enable.")

    yield

    # Shutdown
    logger.info("🛑 Shutting down SHARKMMO Backend...")
    if scheduler_task:
        scheduler_task.cancel()
    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="SHARKMMO API",
    version=settings.APP_VERSION,
    description="Backend API for SHARKMMO Automated MMO Ecosystem",
    lifespan=lifespan
)

# Enable CORS for Next.js Admin Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "slogan": "Hệ sinh thái sản phẩm MMO tự động"
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
