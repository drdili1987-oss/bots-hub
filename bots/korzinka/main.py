"""
Render.com uchun asosiy ishga tushirish fayli.

Render'da (RENDER_EXTERNAL_URL yoki WEBHOOK_URL bor) -> webhook rejimi.
  Bitta aiohttp server ham Telegram webhook'ini, ham health so'rovlarini qabul qiladi.
  Free instance uxlab qolsa, Telegram'dan kelgan birinchi xabar uni uyg'otadi.
Lokal (URL yo'q) -> polling rejimi.

Eslatma: self-ping olib tashlandi. U Free instance'ni 24/7 uyg'oq ushlab,
workspace'ning umumiy 750 soatlik bepul limitini yolg'iz o'zi tugatib qo'yadi.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import bot as bot_module
import config

WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_PATH = "/webhook"
# Telegram faqat [A-Za-z0-9_-] belgilarni qabul qiladi; tokendan barqaror maxfiy kalit yasaymiz
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or "".join(
    c for c in config.BOT_TOKEN.split(":")[-1] if c.isalnum() or c in "_-"
)[:64] or None
PORT = int(os.getenv("PORT", "8080"))


async def health(_: web.Request) -> web.Response:
    return web.Response(text="Bot ishlayapti!")


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    await bot.set_webhook(
        f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    logging.info("Webhook o'rnatildi: %s%s", WEBHOOK_URL, WEBHOOK_PATH)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... ni to'ldiring.")
    if not bot_module.DATABASE_URL:
        logging.warning(
            "DATABASE_URL yo'q: SQLite ishlatiladi. Render diski vaqtinchalik — "
            "server qayta ishga tushganda yoki uxlab qolganda aktlar yo'qoladi!"
        )

    bot_module.init_db()
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(bot_module.router)

    if not WEBHOOK_URL:
        logging.info("Polling rejimi (lokal)")

        async def run_polling() -> None:
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot)

        asyncio.run(run_polling())
        return

    dp.startup.register(on_startup)
    app = web.Application()
    app.router.add_get("/", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
