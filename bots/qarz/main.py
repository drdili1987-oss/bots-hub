import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import database as db
import keyboards as kb
from config import ADMIN_IDS, BOT_TOKEN
import admin
import employee

logger = logging.getLogger(__name__)

common_router = Router(name="common")


@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    role = "admin" if user_id in ADMIN_IDS else "employee"
    full_name = message.from_user.full_name or str(user_id)

    user = await db.get_or_create_user(user_id, full_name, role)

    if user["role"] == "admin":
        await message.answer(
            f"Assalomu alaykum, {full_name}! Admin panelga xush kelibsiz.",
            reply_markup=kb.admin_main_menu(),
        )
    else:
        await message.answer(
            f"Assalomu alaykum, {full_name}! Xodimlar qarz tizimiga xush kelibsiz.",
            reply_markup=kb.employee_main_menu(),
        )


@common_router.message(F.text.in_({"/cancel", kb.BTN_CANCEL}), StateFilter("*"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Bekor qilinadigan hech narsa yo'q.")
        return
    await state.clear()
    user = await db.get_user(message.from_user.id)
    is_admin = user is not None and user.get("role") == "admin"
    menu = kb.admin_main_menu() if is_admin else kb.employee_main_menu()
    await message.answer("Bekor qilindi.", reply_markup=menu)


WEBHOOK_URL = (os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
WEBHOOK_PATH = "/webhook"
# Telegram faqat [A-Za-z0-9_-] belgilarni qabul qiladi; tokendan barqaror maxfiy kalit yasaymiz
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or "".join(
    c for c in BOT_TOKEN.split(":")[-1] if c.isalnum() or c in "_-"
)[:64] or None
PORT = int(os.getenv("PORT", "8080"))


def build() -> tuple[Bot, Dispatcher]:
    db.init_firebase()
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(common_router)
    dp.include_router(admin.router)
    dp.include_router(employee.router)
    return bot, dp


async def health(_: web.Request) -> web.Response:
    return web.Response(text="Bot ishlayapti!")


async def on_startup(bot: Bot, dispatcher: Dispatcher) -> None:
    await bot.set_webhook(
        f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        secret_token=WEBHOOK_SECRET,
        allowed_updates=dispatcher.resolve_used_update_types(),
    )
    logger.info("Webhook o'rnatildi: %s%s", WEBHOOK_URL, WEBHOOK_PATH)


async def run_polling() -> None:
    bot, dp = build()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot ishga tushdi (polling).")
    await dp.start_polling(bot)


def main() -> None:
    """Render web servis (RENDER_EXTERNAL_URL bor) -> webhook; lokal -> polling."""
    logging.basicConfig(level=logging.INFO)
    if not WEBHOOK_URL:
        asyncio.run(run_polling())
        return
    bot, dp = build()
    dp.startup.register(on_startup)
    app = web.Application()
    app.router.add_get("/", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=WEBHOOK_SECRET).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")
