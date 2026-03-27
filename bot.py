import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.db import init_db
from handlers import start, catalog, products, cart, orders, feedback, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("shopbot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


async def main():
    if not BOT_TOKEN:
        raise ValueError("❌ BOT_TOKEN topilmadi! .env faylini tekshiring.")

    logger.info("🚀 ShopBot ishga tushmoqda...")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register routers (order matters — admin first to not conflict)
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(products.router)
    dp.include_router(cart.router)
    dp.include_router(orders.router)
    dp.include_router(feedback.router)

    await init_db()
    logger.info("✅ Database tayyor.")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Bot polling boshlandi.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
