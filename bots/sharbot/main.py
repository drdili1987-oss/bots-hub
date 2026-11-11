"""Sharbot — ishga tushirish.

Render'da (RENDER_EXTERNAL_URL yoki WEBHOOK_URL bor) -> webhook rejimi (Free instance uchun).
Lokal (URL yo'q) -> polling rejimi.

Kunlik 19:00 eslatma:
  * CRON_SECRET o'rnatilgan bo'lsa: ichki taymer O'CHIQ. Eslatmani tashqi cron
    (GitHub Actions, .github/workflows/daily-reminder.yml) GET /cron/daily?key=... orqali chaqiradi.
    Sabab: Free instance uxlab qolsa, ichki asyncio taymer ham "uxlaydi" va eslatma yuborilmaydi.
  * CRON_SECRET bo'lmasa: avvalgidek ichki daily_scheduler (pullik, doimiy instance uchun).
"""
import asyncio
import hmac
import logging
import os
import sys
from datetime import datetime

from aiohttp import web

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN, ADMIN_ID
from database import init_db
import handlers_admin
import handlers_worker
import handlers_xodim
from scheduler import UZT, daily_scheduler, send_tomorrow_notifications

WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_PATH = "/webhook"
# Telegram faqat [A-Za-z0-9_-] qabul qiladi; berilmasa tokendan barqaror kalit yasaladi
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or "".join(
    c for c in (BOT_TOKEN or "").split(":")[-1] if c.isalnum() or c in "_-"
)[:64] or None
CRON_SECRET = os.getenv("CRON_SECRET", "")
PORT = int(os.getenv("PORT", "8080"))

log = logging.getLogger("main")

# Bitta instance ichida bir kunda ikki marta yuborilmasin (cron qayta urinishlari uchun)
_last_cron_date = None
_cron_lock = asyncio.Lock()


def check_config() -> None:
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN sozlanmagan. config.py faylida yoki BOT_TOKEN environment "
            "variable orqali @BotFather bergan tokenni kiriting."
        )
    if ADMIN_ID == 0:
        raise RuntimeError(
            "ADMIN_ID sozlanmagan. config.py faylida yoki ADMIN_ID environment "
            "variable orqali o'zingizning Telegram ID raqamingizni kiriting "
            "(@userinfobot orqali bilib olishingiz mumkin)."
        )


def build() -> tuple[Bot, Dispatcher]:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(handlers_admin.router)
    dp.include_router(handlers_worker.router)
    dp.include_router(handlers_xodim.router)
    return bot, dp


async def health(_: web.Request) -> web.Response:
    return web.Response(text="Bot is running!")


async def cron_daily(request: web.Request) -> web.Response:
    """Tashqi cron chaqiradi: ertangi buyurtmalar eslatmasini yuboradi."""
    global _last_cron_date
    key = request.query.get("key", "")
    if not CRON_SECRET or not hmac.compare_digest(key, CRON_SECRET):
        return web.Response(status=403, text="forbidden")

    today = datetime.now(UZT).date()
    force = request.query.get("force") == "1"
    async with _cron_lock:
        if _last_cron_date == today and not force:
            return web.Response(text=f"already sent for {today}")
        await send_tomorrow_notifications(request.app["bot"])
        _last_cron_date = today
    log.info("Kunlik eslatma tashqi cron orqali yuborildi (%s)", today)
    return web.Response(text=f"sent for {today}")


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    await init_db()
    await bot.set_webhook(
        f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    log.info("Webhook o'rnatildi: %s%s", WEBHOOK_URL, WEBHOOK_PATH)
    if not CRON_SECRET:
        asyncio.create_task(daily_scheduler(bot))
        log.warning("CRON_SECRET yo'q: ichki taymer ishlaydi (Free instance uxlasa, eslatma yuborilmaydi)")


async def run_polling(bot: Bot, dp: Dispatcher) -> None:
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(daily_scheduler(bot))
    await dp.start_polling(bot)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    check_config()
    bot, dp = build()

    if not WEBHOOK_URL:
        log.info("Polling rejimi (lokal)")
        asyncio.run(run_polling(bot, dp))
        return

    dp.startup.register(on_startup)
    app = web.Application()
    app["bot"] = bot
    app.router.add_get("/", health)
    app.router.add_get("/cron/daily", cron_daily)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
