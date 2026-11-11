from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import database as db
from keyboards.default import (
    language_keyboard,
    main_menu_keyboard,
    phone_keyboard,
    remove_keyboard,
    LANGUAGE_BUTTONS,
)
from keyboards.inline import debt_confirm_keyboard
from locales.texts import TEXTS
from states import Registration

router = Router(name="start")


async def send_video_guide(target: Message | Bot, user_id: int, lang: str) -> None:
    t = TEXTS.get(lang, TEXTS["uz"])
    video_file_id = db.get_setting("video_guide_file_id")
    video_url = db.get_setting("video_guide_url", "")

    bot = target if isinstance(target, Bot) else target.bot

    if video_file_id:
        try:
            caption = t.get("video_guide_caption", t.get("video_guide_text", ""))
            await bot.send_video(
                chat_id=user_id,
                video=video_file_id,
                caption=caption,
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

    url_str = video_url if video_url else "https://t.me/qarzoldiberdi_bot"
    text = t.get("video_guide_text", "").format(video_url=url_str)

    if isinstance(target, Message):
        await target.answer(text, parse_mode="HTML", disable_web_page_preview=False)
    else:
        await bot.send_message(user_id, text, parse_mode="HTML", disable_web_page_preview=False)


async def _send_pending_debt_request(bot: Bot, debt_id: str, target_user_id: int) -> None:
    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "pending":
        return

    other_id = debt["creditor_id"] if str(debt.get("debtor_id")) == str(target_user_id) else debt["debtor_id"]
    other_user = db.get_user(other_id) if other_id else None
    lang = db.get_user_language(target_user_id)
    other_name = other_user["full_name"] if other_user else "N/A"

    desc_str = f"\n📝 <b>Izoh:</b> {debt['description']}" if debt.get("description") else ""
    text = (
        TEXTS[lang]["debt_incoming_request"].format(
            name=other_name, amount=db.format_amount(debt["amount"]), currency=debt["currency"]
        )
        + desc_str
    )
    await bot.send_message(int(target_user_id), text, reply_markup=debt_confirm_keyboard(lang, debt_id))


async def _handle_deeplink_after_registration(bot: Bot, user_id: int, payload: str) -> None:
    if not payload.startswith("debt_"):
        return
    debt_id = payload.replace("debt_", "", 1)
    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "pending":
        return

    if debt.get("debtor_id") is None:
        db.set_debt_debtor(debt_id, user_id)
        await _send_pending_debt_request(bot, debt_id, user_id)
    elif debt.get("creditor_id") is None:
        db.set_debt_creditor(debt_id, user_id)
        await _send_pending_debt_request(bot, debt_id, user_id)


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(
    message: Message, command: CommandObject, state: FSMContext, bot: Bot
) -> None:
    await state.clear()
    payload = command.args or ""
    user_id = message.from_user.id

    if db.user_exists(user_id):
        lang = db.get_user_language(user_id)
        await _handle_deeplink_after_registration(bot, user_id, payload)
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    await state.update_data(deep_link_payload=payload)
    await state.set_state(Registration.choosing_language)
    await message.answer(TEXTS["uz"]["choose_language"], reply_markup=language_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    if db.user_exists(user_id):
        lang = db.get_user_language(user_id)
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    await state.set_state(Registration.choosing_language)
    await message.answer(TEXTS["uz"]["choose_language"], reply_markup=language_keyboard())


@router.message(Registration.choosing_language, F.text.in_(LANGUAGE_BUTTONS.keys()))
async def process_language(message: Message, state: FSMContext) -> None:
    lang = LANGUAGE_BUTTONS[message.text]
    await state.update_data(language=lang)
    await state.set_state(Registration.entering_name)
    await message.answer(TEXTS[lang]["name_request"], reply_markup=remove_keyboard())


@router.message(Registration.choosing_language)
async def process_language_invalid(message: Message) -> None:
    await message.answer(TEXTS["uz"]["invalid_language"], reply_markup=language_keyboard())


@router.message(Registration.entering_name, F.text)
async def process_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data["language"]
    full_name = message.text.strip()

    if len(full_name) < 2:
        await message.answer(TEXTS[lang]["invalid_name"])
        return

    await state.update_data(full_name=full_name)
    await state.set_state(Registration.entering_phone)
    await message.answer(TEXTS[lang]["phone_request"], reply_markup=phone_keyboard(lang))


@router.message(Registration.entering_phone, F.content_type == ContentType.CONTACT)
async def process_phone_contact(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data["language"]
    user_id = message.from_user.id

    if message.contact.user_id and message.contact.user_id != user_id:
        await message.answer(TEXTS[lang]["invalid_contact"])
        return

    db.create_user(
        user_id=user_id,
        full_name=data["full_name"],
        phone_number=message.contact.phone_number,
        language=lang,
        username=message.from_user.username or "",
    )

    payload = data.get("deep_link_payload", "")
    await state.clear()

    await message.answer(
        TEXTS[lang]["registered_welcome"].format(name=data["full_name"]),
        reply_markup=main_menu_keyboard(lang),
    )

    await send_video_guide(message, user_id, lang)
    await _handle_deeplink_after_registration(bot, user_id, payload)


@router.message(Registration.entering_phone, F.text)
async def process_phone_text(message: Message, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    lang = data["language"]
    user_id = message.from_user.id
    raw_phone = message.text.strip()

    clean_phone = db.normalize_phone(raw_phone)
    if len(clean_phone) < 9:
        await message.answer(TEXTS[lang]["invalid_phone"], reply_markup=phone_keyboard(lang))
        return

    db.create_user(
        user_id=user_id,
        full_name=data["full_name"],
        phone_number=clean_phone,
        language=lang,
        username=message.from_user.username or "",
    )

    payload = data.get("deep_link_payload", "")
    await state.clear()

    await message.answer(
        TEXTS[lang]["registered_welcome"].format(name=data["full_name"]),
        reply_markup=main_menu_keyboard(lang),
    )

    await send_video_guide(message, user_id, lang)
    await _handle_deeplink_after_registration(bot, user_id, payload)


@router.message(Registration.entering_phone)
async def process_phone_invalid(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data["language"]
    await message.answer(TEXTS[lang]["invalid_phone"], reply_markup=phone_keyboard(lang))
