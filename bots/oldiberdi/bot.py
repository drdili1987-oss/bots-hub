import os
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN
from handlers import admin, debts, finance, start
from services.scheduler import setup_scheduler
from services.userbot import userbot_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def handle_health_check(request):
    return web.Response(text="OK - Bot is running!")


async def start_web_server():
    port = os.getenv("PORT")
    if not port:
        return None
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(port))
    await site.start()
    logger.info(f"Health check web server started on port {port}")
    return runner


async def main() -> None:
    web_runner = await start_web_server()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Handler'lar ro'yxati tartibi muhim: start FSM state'lari eng birinchi
    # tekshiriladi, keyin debts/finance/admin.
    dp.include_router(start.router)
    dp.include_router(debts.router)
    dp.include_router(finance.router)
    dp.include_router(admin.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    await userbot_service.start()

    # Bazadagi foydalanuvchilar va ma'lumotlarni keshga yuklash (tez ishlashi uchun)
    try:
        import database as db
        db.get_all_users()
        logger.info("Foydalanuvchilar keshi muvaffaqiyatli yuklandi.")
    except Exception as e:
        logger.warning(f"Keshni yuklashda xatolik: {e}")

    try:
        logger.info("Bot ishga tushmoqda (long polling)...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await userbot_service.stop()
        scheduler.shutdown(wait=False)
        await bot.session.close()
        if web_runner:
            await web_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
