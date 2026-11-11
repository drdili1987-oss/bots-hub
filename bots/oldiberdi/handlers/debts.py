import json
import re
import urllib.parse
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database as db
from config import BOT_USERNAME
from keyboards.default import (
    cancel_keyboard,
    main_menu_keyboard,
    skip_description_keyboard,
)
from keyboards.inline import (
    add_button_keyboard,
    currency_keyboard,
    debt_actions_keyboard,
    debt_confirm_keyboard,
    debts_interactive_keyboard,
    language_change_keyboard,
    main_menu_inline_keyboard,
    settings_keyboard,
    share_debt_keyboard,
)
from locales.texts import TEXTS
from services.sms import sms_service
from services.userbot import userbot_service
from states import AddDebt, PartialDebtPayment

router = Router(name="debts")

ALL_BTN_CREDITORS = [t["btn_creditors"] for t in TEXTS.values()]
ALL_BTN_DEBTORS = [t["btn_debtors"] for t in TEXTS.values()]
ALL_BTN_HISTORY = [t["btn_history"] for t in TEXTS.values()]
ALL_BTN_CANCEL = [t["btn_cancel"] for t in TEXTS.values()] + ["/cancel", "Bekor qilish", "Отмена"]
ALL_BTN_MAIN_MENU = [t.get("btn_main_menu", "🏠 Asosiy menyu") for t in TEXTS.values()] + [
    "/menu", "Asosiy menyu", "Главное меню", "Басты мәзір"
]
ALL_BTN_SKIP = [t.get("btn_skip", "➡️ O'tkazib yuborish") for t in TEXTS.values()] + [
    "/skip", "O'tkazib yuborish", "Пропустить", "Өткізіп жіберу"
]
ALL_BTN_SETTINGS = [t.get("btn_settings", "⚙️ Sozlamalar") for t in TEXTS.values()]
ALL_BTN_DONAT = [t.get("btn_donat", "💝 Donat") for t in TEXTS.values()]
ALL_BTN_PERSONAL_FINANCE = [t.get("btn_personal_finance", "💼 Shaxsiy moliya") for t in TEXTS.values()] + [
    "Shaxsiy moliya", "Личные финансы", "Жеке қаржы", "Personal Finance", "/finance"
]
ALL_BTN_GUIDE = [t.get("btn_guide", "📹 Qo'llanma") for t in TEXTS.values()] + [
    "📹 Qo'llanma", "📹 Инструкция", "📹 Нұсқаулық", "📹 Video Guide", "/guide", "/video", "Qo'llanma", "Инструкция"
]

@router.message(F.web_app_data)
async def handle_web_app_data(message: Message, state: FSMContext) -> None:
    from handlers.finance import show_personal_finance, show_reports_hub
    await state.clear()
    try:
        raw_data = message.web_app_data.data
        data = json.loads(raw_data)
        action = data.get("action")
        if action == "creditors":
            await show_creditors(message, state)
        elif action == "debtors":
            await show_debtors(message, state)
        elif action == "history":
            await show_history(message, state)
        elif action == "finance":
            await show_personal_finance(message, state)
        elif action == "reports":
            await show_reports_hub(message, state)
        elif action == "settings":
            await show_settings(message, state)
        elif action == "donat":
            await show_donat(message, state)
        else:
            user_id = message.from_user.id
            lang = db.get_user_language(user_id)
            await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
    except Exception:
        user_id = message.from_user.id
        lang = db.get_user_language(user_id)
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))


@router.message(F.text.in_(ALL_BTN_MAIN_MENU))
async def handle_main_menu_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))


@router.callback_query(F.data == "to_main_menu")
async def handle_main_menu_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await callback.message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
    await callback.answer()


@router.message(F.text.in_(ALL_BTN_SETTINGS))
async def show_settings(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await message.answer(TEXTS[lang]["settings_title"], reply_markup=settings_keyboard(lang, user_id=user_id))


@router.message(F.text.in_(ALL_BTN_DONAT))
async def show_donat(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await message.answer(TEXTS[lang]["donat_text"], reply_markup=main_menu_inline_keyboard(lang))


@router.message(F.text.in_(ALL_BTN_GUIDE))
async def show_guide(message: Message, state: FSMContext) -> None:
    from handlers.start import send_video_guide
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    await send_video_guide(message, user_id, lang)


@router.callback_query(F.data == "settings_change_language")
async def settings_change_language(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    await callback.message.edit_text(
        TEXTS[lang]["choose_new_language"], reply_markup=language_change_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "invite_friends")
async def process_invite_friends(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    bot_username = BOT_USERNAME or "qarzoldiberdi_bot"
    
    invite_url = f"https://t.me/{bot_username}?start=ref_{user_id}"
    if lang == "ru":
        invite_msg = (
            f"Здравствуйте! Для удобного учета долгов и взаиморасчетов используйте бота «Temir Daftar»:\n"
            f"👉 {invite_url}"
        )
    elif lang == "kk":
        invite_msg = (
            f"Ассалаумағалейкум! Қарыздарды оңай есептеу үшін «Temir Daftar» ботына қосылыңыз:\n"
            f"👉 {invite_url}"
        )
    elif lang == "en":
        invite_msg = (
            f"Hello! Use the «Temir Daftar» bot for easy debt tracking and records:\n"
            f"👉 {invite_url}"
        )
    else:
        invite_msg = (
            f"Assalomu Alaykum! Qarz va pullarni oson hisob-kitob qilish uchun «Temir Daftar» botiga kiring:\n"
            f"👉 {invite_url}"
        )
    encoded_text = urllib.parse.quote_plus(invite_msg)
    share_url = f"https://t.me/share/url?url={urllib.parse.quote_plus(invite_url)}&text={encoded_text}"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Telegramda ulashish", url=share_url)],
            [InlineKeyboardButton(text=TEXTS[lang].get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")],
        ]
    )
    
    msg_text = (
        "👥 <b>Do'stlarga ulashish</b>\n\n"
        "Quyidagi matnni nusxalashingiz yoki «🚀 Telegramda ulashish» tugmasi orqali do'stlaringizga yuborishingiz mumkin:\n\n"
        f"<code>{invite_msg}</code>"
    )
    await callback.message.answer(msg_text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    new_lang = callback.data.replace("set_lang_", "", 1)
    if new_lang not in ("uz", "ru", "kk", "en"):
        await callback.answer("Noto'g'ri til!", show_alert=True)
        return
    db.update_user_language(user_id, new_lang)
    await callback.message.edit_text(TEXTS[new_lang]["language_changed"])
    await callback.message.answer(
        TEXTS[new_lang]["main_menu_title"], reply_markup=main_menu_keyboard(new_lang)
    )
    await callback.answer()


@router.message(F.text.in_(ALL_BTN_CREDITORS))
async def show_creditors(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    debts = [d for d in db.get_debts_by_debtor(user_id) if d.get("status") in ("active", "pending")]

    if not debts:
        await message.answer(TEXTS[lang]["no_creditors"], reply_markup=debts_interactive_keyboard(lang, "creditor"))
        return

    lines = [TEXTS[lang]["creditors_title"]]
    active_list = []
    pending_list = []
    for d in debts:
        name = db.get_debt_party_name(d, user_id)
        status_text = (
            TEXTS[lang]["status_pending"] if d["status"] == "pending" else TEXTS[lang]["status_active"]
        )
        desc_text = f" — <i>{d['description']}</i>" if d.get("description") else ""
        lines.append(f"• <b>{name}</b>: {db.format_amount(d['amount'])} {d['currency']} [{status_text}]{desc_text}")
        item = {"debt_id": d["debt_id"], "name": name, "amount": d["amount"], "currency": d["currency"]}
        if d.get("status") == "pending":
            pending_list.append(item)
        else:
            active_list.append(item)

    lines.append("\n👇 <i>Batafsil ko'rish, qarzni yopish yoki o'zgartirish uchun kerakli haqdor ustiga bosing:</i>")
    await message.answer(
        "\n".join(lines), 
        reply_markup=debts_interactive_keyboard(lang, "creditor", active_debts=active_list, pending_debts=pending_list)
    )


@router.message(F.text.in_(ALL_BTN_DEBTORS))
async def show_debtors(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    debts = [d for d in db.get_debts_by_creditor(user_id) if d.get("status") in ("active", "pending")]

    if not debts:
        await message.answer(TEXTS[lang]["no_debtors"], reply_markup=debts_interactive_keyboard(lang, "debtor"))
        return

    lines = [TEXTS[lang]["debtors_title"]]
    active_list = []
    pending_list = []
    for d in debts:
        name = db.get_debt_party_name(d, user_id)
        status_text = (
            TEXTS[lang]["status_pending"] if d["status"] == "pending" else TEXTS[lang]["status_active"]
        )
        desc_text = f" — <i>{d['description']}</i>" if d.get("description") else ""
        lines.append(f"• <b>{name}</b>: {db.format_amount(d['amount'])} {d['currency']} [{status_text}]{desc_text}")
        item = {"debt_id": d["debt_id"], "name": name, "amount": d["amount"], "currency": d["currency"]}
        if d.get("status") == "pending":
            pending_list.append(item)
        else:
            active_list.append(item)

    lines.append("\n👇 <i>Batafsil ko'rish, qarzni yopish yoki eslatma yuborish uchun kerakli qarzdor ustiga bosing:</i>")
    await message.answer(
        "\n".join(lines), 
        reply_markup=debts_interactive_keyboard(lang, "debtor", active_debts=active_list, pending_debts=pending_list)
    )


# ==================== QARZNI BOSGANDA BATAFSIL KO'RISH VA AMALLAR ====================

@router.callback_query(F.data.startswith("debt_view_"))
async def view_debt_detail(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    debt_id = callback.data.replace("debt_view_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer("Qarz topilmadi yoki o'chirilgan!", show_alert=True)
        return

    is_creditor = str(debt.get("creditor_id")) == str(user_id)
    role = "debtor" if is_creditor else "creditor"
    other_name = db.get_debt_party_name(debt, user_id)
    
    status = debt.get("status", "active")
    status_label = "🟢 Faol (yopilmagan)" if status == "active" else ("🟡 Kutilmoqda (tasdiqlanmagan)" if status == "pending" else "🔴 Yopilgan")
    
    role_desc = "Men qarz berganman (Haqdorman)" if is_creditor else "Men qarz olganman (Qarzdorman)"
    
    desc = debt.get("description") or "Mavjud emas"
    due_date = debt.get("due_date") or "Belgilanmagan"
    created = debt.get("created_at", "")
    if created and "T" in created:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            created = dt.strftime("%d.%m.%Y %H:%M")
        except Exception:
            pass

    text = (
        f"📄 <b>Qarz ma'lumotlari:</b>\n\n"
        f"👤 <b>Ikkinchi tomon:</b> {other_name}\n"
        f"📌 <b>Mening rolim:</b> {role_desc}\n"
        f"💰 <b>Qarz summasi:</b> <b>{db.format_amount(debt['amount'])} {debt['currency']}</b>\n"
        f"📊 <b>Holati:</b> {status_label}\n"
        f"📝 <b>Izoh:</b> <i>{desc}</i>\n"
        f"📅 <b>Qaytarish muddati:</b> {due_date}\n"
        f"⏱ <b>Yaratilgan:</b> {created}\n"
    )

    await callback.message.edit_text(text, reply_markup=debt_actions_keyboard(debt_id, role, status, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("debt_close_"))
async def close_debt_handler(callback: CallbackQuery, bot: Bot) -> None:
    debt_id = callback.data.replace("debt_close_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer("Qarz topilmadi!", show_alert=True)
        return

    amount = debt.get("amount", 0)
    currency = debt.get("currency", "UZS")
    other_id = debt.get("debtor_id") if str(debt.get("creditor_id")) == str(user_id) else debt.get("creditor_id")
    other_name = db.get_debt_party_name(debt, user_id)

    # Statusni closed ga o'zgartiramiz
    db.update_debt_status(debt_id, "closed")
    
    # Tarixga qo'shamiz
    db.add_history(
        debt_id=debt_id,
        from_user=debt.get("debtor_id") or user_id,
        to_user=debt.get("creditor_id") or user_id,
        type_="lend" if str(debt.get("creditor_id")) == str(user_id) else "borrow",
        amount=amount,
        currency=currency,
        status="closed",
    )

    await callback.answer("✅ Qarz muvaffaqiyatli yopildi!", show_alert=True)
    
    success_text = (
        f"✅ <b>Qarz to'liq yopildi!</b>\n\n"
        f"👤 <b>Ikkinchi tomon:</b> {other_name}\n"
        f"💰 <b>Yopilgan summa:</b> {db.format_amount(amount)} {currency}\n"
        f"📊 <b>Yangi holat:</b> 🔴 Yopilgan"
    )
    
    is_creditor = str(debt.get("creditor_id")) == str(user_id)
    role = "debtor" if is_creditor else "creditor"
    await callback.message.edit_text(
        success_text,
        reply_markup=debt_actions_keyboard(debt_id, role, "closed", lang)
    )

    # Agar ikkinchi tomon ro'yxatdan o'tgan bo'lsa, unga xabarnoma yuboramiz
    if other_id and str(other_id) != str(user_id):
        try:
            other_lang = db.get_user_language(other_id)
            me_user = db.get_user(user_id)
            me_name = me_user.get("full_name", "Hamkoringiz") if me_user else "Hamkoringiz"
            notify_msg = (
                f"🤝 <b>Qarz yopildi!</b>\n\n"
                f"<b>{me_name}</b> siz bilan bo'lgan <b>{db.format_amount(amount)} {currency}</b> miqdoridagi qarzni to'liq yopilgan deb belgiladi."
            )
            await bot.send_message(int(other_id), notify_msg)
        except Exception:
            pass


@router.callback_query(F.data.startswith("debt_part_"))
async def start_partial_payment(callback: CallbackQuery, state: FSMContext) -> None:
    debt_id = callback.data.replace("debt_part_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "active":
        await callback.answer("Bu qarz faol emas!", show_alert=True)
        return

    await state.set_state(PartialDebtPayment.entering_amount)
    await state.update_data(debt_id=debt_id)

    other_name = db.get_debt_party_name(debt, user_id)
    text = (
        f"💸 <b>Qisman to'lash / kamaytirish:</b>\n\n"
        f"👤 Shaxs: <b>{other_name}</b>\n"
        f"💰 Hozirgi qarz: <b>{db.format_amount(debt['amount'])} {debt['currency']}</b>\n\n"
        f"Qancha summa to'landi / qaytarildi? (Masalan: <code>200 000</code> yoki <code>50k</code>):"
    )
    await callback.message.answer(text, reply_markup=cancel_keyboard(lang))
    await callback.answer()


@router.message(PartialDebtPayment.entering_amount, F.text)
async def process_partial_amount(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    paid = db.parse_amount(message.text)
    if not paid or paid <= 0:
        await message.answer(TEXTS[lang]["invalid_amount"], reply_markup=cancel_keyboard(lang))
        return

    data = await state.get_data()
    debt_id = data.get("debt_id")
    await state.clear()

    debt = db.get_debt(debt_id)
    if not debt:
        await message.answer("Qarz topilmadi!", reply_markup=main_menu_keyboard(lang))
        return

    current_amount = float(debt.get("amount", 0))
    currency = debt.get("currency", "UZS")
    other_id = debt.get("debtor_id") if str(debt.get("creditor_id")) == str(user_id) else debt.get("creditor_id")
    other_name = db.get_debt_party_name(debt, user_id)

    new_amount = max(0.0, current_amount - paid)

    if new_amount <= 0:
        db.update_debt_amount(debt_id, 0)
        db.update_debt_status(debt_id, "closed")
        status_msg = "Qarz to'liq yopildi! ✅"
    else:
        db.update_debt_amount(debt_id, new_amount)
        status_msg = f"Qoldiq qarz: <b>{db.format_amount(new_amount)} {currency}</b>"

    # Tarixga qo'shamiz
    db.add_history(
        debt_id=debt_id,
        from_user=debt.get("debtor_id") or user_id,
        to_user=debt.get("creditor_id") or user_id,
        type_="lend" if str(debt.get("creditor_id")) == str(user_id) else "borrow",
        amount=paid,
        currency=currency,
        status="partial_paid",
    )

    resp_text = (
        f"✅ <b>To'lov qabul qilindi!</b>\n\n"
        f"👤 <b>Ikkinchi tomon:</b> {other_name}\n"
        f"💸 <b>To'langan summa:</b> -{db.format_amount(paid)} {currency}\n"
        f"📊 <b>Holat:</b> {status_msg}"
    )
    await message.answer(resp_text, reply_markup=main_menu_keyboard(lang))

    # Xabarnoma
    if other_id and str(other_id) != str(user_id):
        try:
            other_lang = db.get_user_language(other_id)
            me_user = db.get_user(user_id)
            me_name = me_user.get("full_name", "Hamkoringiz") if me_user else "Hamkoringiz"
            notify_msg = (
                f"💸 <b>Qarz to'lovi qayd etildi!</b>\n\n"
                f"<b>{me_name}</b> bilan hisob-kitobda <b>{db.format_amount(paid)} {currency}</b> to'lov qayd etildi.\n"
                f"📊 Yangi qoldiq: <b>{db.format_amount(new_amount)} {currency}</b>"
            )
            await bot.send_message(int(other_id), notify_msg)
        except Exception:
            pass


@router.callback_query(F.data.startswith("debt_remind_"))
async def send_manual_debt_reminder(callback: CallbackQuery, bot: Bot) -> None:
    debt_id = callback.data.replace("debt_remind_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "active":
        await callback.answer("Faqat faol qarzlarga eslatma yuborish mumkin!", show_alert=True)
        return

    other_id = debt.get("debtor_id") if str(debt.get("creditor_id")) == str(user_id) else debt.get("creditor_id")
    amount_str = f"{db.format_amount(debt['amount'])} {debt['currency']}"
    me_user = db.get_user(user_id)
    me_name = me_user.get("full_name", "Haqdoringiz") if me_user else "Haqdoringiz"

    sent = False
    if other_id and str(other_id) != str(user_id):
        try:
            other_lang = db.get_user_language(other_id)
            remind_text = (
                f"🔔 <b>Qarz eslatmasi!</b>\n\n"
                f"Hurmatli foydalanuvchi, <b>{me_name}</b> bilan bo'lgan <b>{amount_str}</b> miqdoridagi qarz eslatilmoqda.\n"
                f"📝 Izoh: <i>{debt.get('description', 'Mavjud emas')}</i>"
            )
            await bot.send_message(int(other_id), remind_text)
            sent = True
        except Exception:
            pass

    # Agar bot orqali bormasa, userbot orqali urinamiz
    if not sent:
        target = debt.get("phone") or (str(other_id) if other_id else "")
        if target and userbot_service.is_active():
            remind_text = (
                f"Assalomu alaykum! {me_name} tomonidan Temir Daftar boti orqali qarz eslatmasi yuborildi.\n"
                f"Miqdor: {amount_str}\nIzoh: {debt.get('description', '')}"
            )
            ok, _, _ = await userbot_service.send_pm(target, remind_text)
            sent = ok

    if sent:
        await callback.answer("✅ Eslatma muvaffaqiyatli yuborildi!", show_alert=True)
    else:
        await callback.answer("Eslatma yuborib bo'lmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).", show_alert=True)


@router.callback_query(F.data.startswith("debt_del_"))
async def delete_debt_handler(callback: CallbackQuery) -> None:
    debt_id = callback.data.replace("debt_del_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer("Qarz topilmadi yoki allaqachon o'chirilgan.", show_alert=True)
        return

    if debt.get("status") != "closed":
        await callback.answer(
            "⚠️ Faol qarzni o'chirib bo'lmaydi! Qarz faqat u to'liq qaytarib yopilgandagina ro'yxatdan o'chadi.",
            show_alert=True,
        )
        return

    db.delete_debt(debt_id)
    await callback.answer("🗑 Qarz o'chirildi!", show_alert=True)
    await callback.message.edit_text(
        "🗑 <b>Qarz butunlay o'chirildi.</b>",
        reply_markup=main_menu_inline_keyboard(lang)
    )


@router.callback_query(F.data.startswith("debt_reopen_"))
async def reopen_debt_handler(callback: CallbackQuery) -> None:
    debt_id = callback.data.replace("debt_reopen_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer("Qarz topilmadi!", show_alert=True)
        return

    db.update_debt_status(debt_id, "active")
    await callback.answer("🟢 Qarz qayta faollashtirildi!", show_alert=True)
    
    is_creditor = str(debt.get("creditor_id")) == str(user_id)
    role = "debtor" if is_creditor else "creditor"
    await callback.message.edit_text(
        "🟢 <b>Qarz qayta faol holatga keltirildi.</b>",
        reply_markup=debt_actions_keyboard(debt_id, role, "active", lang)
    )


@router.callback_query(F.data.startswith("debt_back_"))
async def back_to_debts_list(callback: CallbackQuery, state: FSMContext) -> None:
    role = callback.data.replace("debt_back_", "", 1)
    if role == "creditor":
        await show_creditors(callback.message, state)
    else:
        await show_debtors(callback.message, state)
    await callback.answer()


@router.message(F.text.in_(ALL_BTN_HISTORY))
async def show_history(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    # To'lov tarixi
    history = db.get_history_by_user(user_id)

    # Barcha qarzlar (yakunlangan va faol)
    all_debts_as_debtor = db.get_debts_by_debtor(user_id)
    all_debts_as_creditor = db.get_debts_by_creditor(user_id)

    if not history and not all_debts_as_debtor and not all_debts_as_creditor:
        await message.answer(TEXTS[lang]["no_history"], reply_markup=main_menu_inline_keyboard(lang))
        return

    lines = [TEXTS[lang]["history_title"]]

    # 1) Qarzlar tarixi (kim olgan / kimga bergan)
    debt_lines = []
    for d in all_debts_as_debtor:
        creditor_name = db.get_debt_party_name(d, user_id)
        status = d.get("status", "")
        if status == "active":
            status_emoji = "🟢"
            status_text = TEXTS[lang]["status_active"]
        elif status == "pending":
            status_emoji = "🟡"
            status_text = TEXTS[lang]["status_pending"]
        elif status == "closed":
            status_emoji = "🔴"
            status_text = "yopilgan"
        else:
            status_emoji = "⚪"
            status_text = status
        desc = f" — <i>{d['description']}</i>" if d.get("description") else ""
        ts_raw = d.get("created_at") or d.get("timestamp") or ""
        ts = db.format_date(ts_raw)
        date_str = f" ({ts})" if ts else ""
        debt_lines.append(
            f"{status_emoji} ⬆️ <b>{creditor_name}</b>dan oldim: "
            f"<b>{db.format_amount(d['amount'])} {d['currency']}</b> [{status_text}]{desc}{date_str}"
        )

    for d in all_debts_as_creditor:
        debtor_name = db.get_debt_party_name(d, user_id)
        status = d.get("status", "")
        if status == "active":
            status_emoji = "🟢"
            status_text = TEXTS[lang]["status_active"]
        elif status == "pending":
            status_emoji = "🟡"
            status_text = TEXTS[lang]["status_pending"]
        elif status == "closed":
            status_emoji = "🔴"
            status_text = "yopilgan"
        else:
            status_emoji = "⚪"
            status_text = status
        desc = f" — <i>{d['description']}</i>" if d.get("description") else ""
        ts_raw = d.get("created_at") or d.get("timestamp") or ""
        ts = db.format_date(ts_raw)
        date_str = f" ({ts})" if ts else ""
        debt_lines.append(
            f"{status_emoji} ⬇️ <b>{debtor_name}</b>ga berdim: "
            f"<b>{db.format_amount(d['amount'])} {d['currency']}</b> [{status_text}]{desc}{date_str}"
        )

    if debt_lines:
        lines.append("")
        lines.append("📋 <b>Qarzlar:</b>")
        lines.extend(debt_lines[:20])

    # 2) To'lovlar tarixi
    if history:
        lines.append("")
        lines.append("💰 <b>To'lovlar:</b>")
        for h in history[:20]:
            from_id = h.get("from_user")
            to_id = h.get("to_user")
            if str(from_id) == str(user_id):
                other = db.get_user(to_id)
                other_name = other["full_name"] if other else "N/A"
                direction = f"➡️ <b>{other_name}</b>ga to'ladim"
            else:
                other = db.get_user(from_id)
                other_name = other["full_name"] if other else "N/A"
                direction = f"⬅️ <b>{other_name}</b>dan oldim"

            # Qarz izohi
            debt = db.get_debt(h.get("debt_id", ""))
            desc = ""
            if debt and debt.get("description"):
                desc = f" — <i>{debt['description']}</i>"

            status_text = "✅" if h.get("status") == "confirmed" else "⏳"
            ts_raw = h.get("timestamp") or ""
            ts = db.format_date(ts_raw)
            date_str = f" ({ts})" if ts else ""
            lines.append(
                f"{status_text} {direction}: <b>{db.format_amount(h['amount'])} {h['currency']}</b>{desc}{date_str}"
            )

    await message.answer("\n".join(lines), reply_markup=main_menu_inline_keyboard(lang))


@router.callback_query(F.data.startswith("add_debt_"))
async def start_add_debt(callback: CallbackQuery, state: FSMContext) -> None:
    role = callback.data.replace("add_debt_", "", 1)  # "creditor" yoki "debtor"
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.update_data(role=role)
    await state.set_state(AddDebt.entering_recipient)
    await callback.message.answer(TEXTS[lang]["enter_recipient"], reply_markup=cancel_keyboard(lang))
    await callback.answer()


async def _process_recipient(
    message: Message, state: FSMContext, target_id, target_phone: Optional[str] = None
) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if target_id is not None and str(target_id) == str(user_id):
        await message.answer(TEXTS[lang]["cannot_add_self"])
        return

    if target_phone:
        my_user = db.get_user(user_id)
        if my_user and db.normalize_phone(my_user.get("phone_number", "")) == db.normalize_phone(target_phone):
            await message.answer(TEXTS[lang]["cannot_add_self"])
            return

    await state.update_data(target_id=target_id, target_phone=target_phone)
    await state.set_state(AddDebt.entering_alias)
    await message.answer(TEXTS[lang]["enter_alias"], reply_markup=skip_description_keyboard(lang))


@router.message(AddDebt.entering_alias, F.text)
async def add_debt_alias(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU:
        await state.clear()
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    if message.text in ALL_BTN_CREDITORS:
        await state.clear()
        await show_creditors(message, state)
        return

    if message.text in ALL_BTN_DEBTORS:
        await state.clear()
        await show_debtors(message, state)
        return

    if message.text in ALL_BTN_HISTORY:
        await state.clear()
        await show_history(message, state)
        return

    if message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    alias = ""
    if message.text not in ALL_BTN_SKIP:
        alias = message.text.strip()

    await state.update_data(alias=alias)
    await state.set_state(AddDebt.choosing_currency)
    await message.answer(TEXTS[lang]["choose_currency"], reply_markup=currency_keyboard(lang))


@router.message(AddDebt.entering_recipient, F.content_type == ContentType.CONTACT)
async def add_debt_recipient_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    phone = db.normalize_phone(contact.phone_number)
    target_id = contact.user_id

    if not target_id and phone:
        found = db.find_user_by_phone(phone)
        if found:
            target_id = found.get("user_id")

    await _process_recipient(message, state, target_id, target_phone=phone)


@router.message(AddDebt.entering_recipient, F.text)
async def add_debt_recipient_text(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU:
        await state.clear()
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    if message.text in ALL_BTN_CREDITORS:
        await state.clear()
        await show_creditors(message, state)
        return

    if message.text in ALL_BTN_DEBTORS:
        await state.clear()
        await show_debtors(message, state)
        return

    if message.text in ALL_BTN_HISTORY:
        await state.clear()
        await show_history(message, state)
        return

    if message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    text = message.text.strip()
    target_id = None
    target_phone = None

    if text.startswith("@"):
        found = db.find_user_by_username(text)
        if found:
            target_id = found["user_id"]
            target_phone = db.normalize_phone(found.get("phone_number", ""))
        await state.update_data(target_username=text)
        await _process_recipient(message, state, target_id, target_phone=target_phone)
        return

    clean_digits = re.sub(r"\D", "", text)

    # 1. '+' belgisi yoki ajratuvchilar bilan yozilgan bo'lsa (masalan: +998901234567, +998 90 123 45 67):
    if text.startswith("+") or any(char in text for char in " ()-."):
        if len(clean_digits) in (9, 12):
            target_phone = db.normalize_phone(clean_digits)
            found = db.find_user_by_phone(target_phone)
            if found:
                target_id = found.get("user_id")
            await _process_recipient(message, state, target_id, target_phone=target_phone)
            return

    # 2. 9 ta raqam bo'lsa va O'zbekiston kodi bilan boshlansa (masalan: 901234567, 977774311):
    if len(clean_digits) == 9 and clean_digits[:2] in (
        "90", "91", "93", "94", "95", "97", "98", "99", "88", "33", "77", "50", "20", "29", "71", "78"
    ):
        target_phone = "998" + clean_digits
        found = db.find_user_by_phone(target_phone)
        if found:
            target_id = found.get("user_id")
        await _process_recipient(message, state, target_id, target_phone=target_phone)
        return

    # 3. 12 ta raqam bo'lsa va 998 bilan boshlansa (masalan: 998977774311):
    if len(clean_digits) == 12 and clean_digits.startswith("998"):
        target_phone = clean_digits
        found = db.find_user_by_phone(target_phone)
        if found:
            target_id = found.get("user_id")
        await _process_recipient(message, state, target_id, target_phone=target_phone)
        return

    # 4. Aks holda Telegram ID yoki bazadagi mavjud telefon/user tekshiruvi:
    if text.lstrip("-").isdigit():
        found_by_phone = db.find_user_by_phone(text)
        if found_by_phone:
            target_id = found_by_phone.get("user_id")
            target_phone = db.normalize_phone(found_by_phone.get("phone_number", ""))
        else:
            target_id = int(text)
            existing_user = db.get_user(target_id)
            if existing_user:
                target_phone = db.normalize_phone(existing_user.get("phone_number", ""))

    await _process_recipient(message, state, target_id, target_phone=target_phone)


@router.callback_query(AddDebt.choosing_currency, F.data.startswith("currency_"))
async def add_debt_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.replace("currency_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.update_data(currency=currency)
    await state.set_state(AddDebt.entering_amount)
    await callback.message.answer(TEXTS[lang]["enter_amount"], reply_markup=cancel_keyboard(lang))
    await callback.answer()


@router.message(AddDebt.entering_amount, F.text)
async def add_debt_amount(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU:
        await state.clear()
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    if message.text in ALL_BTN_CREDITORS:
        await state.clear()
        await show_creditors(message, state)
        return

    if message.text in ALL_BTN_DEBTORS:
        await state.clear()
        await show_debtors(message, state)
        return

    if message.text in ALL_BTN_HISTORY:
        await state.clear()
        await show_history(message, state)
        return

    if message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    amount = db.parse_amount(message.text)
    if not amount or amount <= 0:
        await message.answer(TEXTS[lang]["invalid_amount"], reply_markup=cancel_keyboard(lang))
        return

    await state.update_data(amount=amount)
    await state.set_state(AddDebt.entering_description)
    await message.answer(
        TEXTS[lang]["enter_description"],
        reply_markup=skip_description_keyboard(lang),
    )


@router.message(AddDebt.entering_description, F.text)
async def add_debt_description(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU:
        await state.clear()
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return

    if message.text in ALL_BTN_CREDITORS:
        await state.clear()
        await show_creditors(message, state)
        return

    if message.text in ALL_BTN_DEBTORS:
        await state.clear()
        await show_debtors(message, state)
        return

    if message.text in ALL_BTN_HISTORY:
        await state.clear()
        await show_history(message, state)
        return

    if message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    description = ""
    if message.text not in ALL_BTN_SKIP:
        description = message.text.strip()

    await state.update_data(description=description)
    await state.set_state(AddDebt.entering_due_date)
    
    from keyboards.default import due_date_keyboard
    await message.answer(TEXTS[lang].get("enter_due_date", "Qarz qaytarish muddatini tanlang yoki KK.OO.YYYY formatida kiriting (masalan: 31.12.2026):"), reply_markup=due_date_keyboard(lang))

@router.message(AddDebt.entering_due_date, F.text)
async def add_debt_due_date(message: Message, state: FSMContext, bot: Bot) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    
    if message.text in ALL_BTN_MAIN_MENU:
        await state.clear()
        await message.answer(TEXTS[lang]["main_menu_title"], reply_markup=main_menu_keyboard(lang))
        return
    if message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return
        
    text = message.text.strip()
    due_date = None
    
    from datetime import datetime, timedelta
    now = datetime.now()
    
    if text == TEXTS[lang].get("btn_1_week", "1 hafta") or text in ["1 hafta", "1 неделя", "1 апта", "1 week"]:
        due_date = (now + timedelta(days=7)).strftime("%d.%m.%Y")
    elif text == TEXTS[lang].get("btn_1_month", "1 oy") or text in ["1 oy", "1 месяц", "1 ай", "1 month"]:
        due_date = (now + timedelta(days=30)).strftime("%d.%m.%Y")
    elif text == TEXTS[lang].get("btn_no_due_date", "Muddat yo'q") or text in ALL_BTN_SKIP or text in ["Muddat yo'q", "Без срока", "Мерзімсіз", "No due date"]:
        due_date = None
    else:
        clean_date_text = text.replace("/", ".").replace("-", ".")
        parsed = None
        for fmt in ("%d.%m.%Y", "%Y.%m.%d"):
            try:
                parsed = datetime.strptime(clean_date_text, fmt)
                break
            except ValueError:
                pass

        if parsed:
            due_date = parsed.strftime("%d.%m.%Y")
        else:
            invalid_msg = TEXTS[lang].get(
                "invalid_due_date",
                "Noto'g'ri sana formati. Iltimos, muddatni KK.OO.YYYY formatida kiriting (masalan: 31.12.2026) yoki quyidagi tugmalardan birini tanlang:"
            )
            await message.answer(invalid_msg, reply_markup=due_date_keyboard(lang))
            return

    data = await state.get_data()
    await state.clear()
    
    description = data.get("description", "")
    alias = data.get("alias", "")
    role = data["role"]
    target_id = data.get("target_id")
    target_phone = data.get("target_phone")
    target_username = data.get("target_username")
    currency = data["currency"]
    amount = data["amount"]

    target_user_in_db = False
    if target_id is not None:
        target_user_in_db = db.user_exists(target_id)
    if not target_user_in_db and target_phone:
        found_u = db.find_user_by_phone(target_phone)
        if found_u:
            target_id = found_u.get("user_id")
            target_user_in_db = True
    if not target_user_in_db and target_username:
        found_u = db.find_user_by_username(target_username)
        if found_u:
            target_id = found_u.get("user_id")
            target_user_in_db = True

    if role == "creditor":
        debtor_id, creditor_id = user_id, target_id
    else:
        debtor_id, creditor_id = target_id, user_id

    desc_line = f"\n📝 <b>Izoh:</b> {description}" if description else ""
    desc_sms = f"\nIzoh: {description}" if description else ""
    due_line = f"\n⏳ <b>Muddat:</b> {due_date}" if due_date else ""
    due_sms = f"\nMuddat: {due_date}" if due_date else ""

    sent_direct = False
    debt_id = None

    # 1. Agar ikkinchi tomon botga start bergan bo'lsa -> to'g'ridan-to'g'ri bot orqali xabar boradi
    if target_user_in_db and target_id:
        debt_id = db.create_debt(
            debtor_id=debtor_id,
            creditor_id=creditor_id,
            amount=amount,
            currency=currency,
            status="pending",
            phone=target_phone,
            description=description,
            due_date=due_date,
            creator_id=user_id,
            creator_alias=alias,
        )
        other_lang = db.get_user_language(target_id)
        requester = db.get_user(user_id)
        req_name = requester["full_name"] if requester else message.from_user.full_name
        role_text = (
            TEXTS[other_lang]["role_creditor"] if role == "creditor" else TEXTS[other_lang]["role_debtor"]
        )
        
        bot_notify_text = (
            TEXTS[other_lang].get(
                "debt_confirm_request",
                "<b>{name}</b> sizga yangi qarz so'rovi yubordi.\nMiqdor: {amount} {currency}"
            ).format(
                name=req_name,
                role=role_text,
                amount=db.format_amount(amount),
                currency=currency,
                due_date=due_date or "Belgilanmagan",
            )
            + desc_line
        )

        try:
            await bot.send_message(int(target_id), bot_notify_text, reply_markup=debt_confirm_keyboard(other_lang, debt_id))
            sent_direct = True
        except Exception:
            sent_direct = False

    if sent_direct:
        cancel_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ So'rovni bekor qilish", callback_data=f"debt_cancel_creator_{debt_id}")],
                [InlineKeyboardButton(text=TEXTS[lang].get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")],
            ]
        )
        await message.answer(TEXTS[lang]["debt_request_sent"], reply_markup=main_menu_keyboard(lang))
        await message.answer("So'rov holati: ⏳ Tasdiqlanishi kutilmoqda", reply_markup=cancel_kb)
        return

    # 2. Agar botga hali start bermagan bo'lsa (yoki to'g'ridan-to'g'ri bot xabari bormasa) -> Telegram ulashish / SMS ga yo'naltirish
    if not debt_id:
        debt_id = db.create_debt(
            debtor_id=debtor_id,
            creditor_id=creditor_id,
            amount=amount,
            currency=currency,
            status="pending",
            phone=target_phone,
            description=description,
            due_date=due_date,
            creator_id=user_id,
            creator_alias=alias,
        )

    link = f"https://t.me/{BOT_USERNAME}?start=debt_{debt_id}"
    requester = db.get_user(user_id)
    req_name = requester["full_name"] if requester else message.from_user.full_name

    share_text = (
        f"Assalomu alaykum! {req_name} siz bilan Qarz Oldi-Berdi botida hisob-kitob kiritdi.\n"
        f"💰 Summa: {db.format_amount(amount)} {currency}{desc_sms}{due_sms}\n\n"
        f"Batafsil ko'rish va tasdiqlash uchun botga kiring:\n👉 {link}"
    )

    # Userbot PM (agar userbot faol va target mavjud bo'lsa)
    sent_via_pm = False
    target_entity = target_phone or target_username or (str(target_id) if target_id else "")
    if userbot_service.is_active() and target_entity:
        pm_text = (
            f"🤝 <b>Qarz Oldi-Berdi</b>\n\n"
            f"<b>{req_name}</b> sizga <b>{db.format_amount(amount)} {currency}</b> qarz so'rovi kiritdi.{desc_line}{due_line}\n\n"
            f"Batafsil ko'rish va tasdiqlash uchun quyidagi havola orqali botga kiring:\n🔗 {link}"
        )
        ok, status_msg, found_uid = await userbot_service.send_pm(target_entity, pm_text)
        if ok:
            sent_via_pm = True
            if found_uid:
                if role == "creditor":
                    db.set_debt_creditor(debt_id, found_uid)
                else:
                    db.set_debt_debtor(debt_id, found_uid)

    # SMS service gateway orqali jo'natish (agar raqam va sms_service mavjud bo'lsa)
    sms_gateway_sent = False
    if target_phone and not sent_via_pm:
        ok_sms, _ = await sms_service.send_sms(target_phone, share_text)
        if ok_sms:
            sms_gateway_sent = True

    kb = share_debt_keyboard(link, share_text, target_phone or "", lang=lang, debt_id=debt_id)

    if sent_via_pm:
        await message.answer(
            f"✅ <b>Foydalanuvchining Telegram shaxsiy chatiga (lichkasiga) taklif xabari yuborildi!</b>{desc_line}{due_line}\n\n"
            f"U botga kirib tasdiqlagach, qarz faol holatga o'tadi.\n\n"
            f"Taklif havolasi:\n<code>{link}</code>",
            reply_markup=main_menu_keyboard(lang),
        )
    elif sms_gateway_sent:
        await message.answer(
            TEXTS[lang]["sms_sent"].format(phone=target_phone, link=link),
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await message.answer(
            f"📲 <b>Foydalanuvchi botga hali start bermagan.</b>\n\n"
            f"💰 Summa: <b>{db.format_amount(amount)} {currency}</b>{desc_line}{due_line}\n\n"
            f"Qarz so'rovini yuborish uchun quyidagi tugmalardan birini bosing:\n"
            f"• <b>✈️ Telegramda ulashish:</b> Telegram chatlari orqali ulashish\n"
            f"• <b>📱 SMS orqali ulashish:</b> Agar u Telegramda bo'lmasa, SMS ga yo'naltirish\n\n"
            f"🔗 <b>Qarz havolasi:</b>\n<code>{link}</code>",
            reply_markup=main_menu_keyboard(lang),
        )

    await message.answer("Tezkor amallar va ulashish:", reply_markup=kb)


@router.callback_query(F.data.startswith("debt_cancel_creator_"))
async def cancel_pending_debt_by_creator(callback: CallbackQuery) -> None:
    debt_id = callback.data.replace("debt_cancel_creator_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer("Bu qarz topilmadi yoki allaqachon bekor qilingan.", show_alert=True)
        try:
            await callback.message.delete()
        except Exception:
            pass
        return

    # Faqat qarz yaratuvchisi va faqat pending holatda bekor qila oladi
    if str(debt.get("debtor_id")) != str(user_id) and str(debt.get("creditor_id")) != str(user_id):
        await callback.answer("Siz ushbu so'rovni bekor qila olmaysiz.", show_alert=True)
        return

    if debt.get("status") != "pending":
        await callback.answer("Ushbu qarz allaqachon tasdiqlangan yoki yopilgan.", show_alert=True)
        return

    db.delete_debt(debt_id)
    await callback.answer("✅ Qarz so'rovi bekor qilindi!", show_alert=True)
    try:
        await callback.message.edit_text(
            f"❌ <b>Qarz so'rovi bekor qilindi va o'chirildi.</b>\nMiqdor: {db.format_amount(debt['amount'])} {debt['currency']}",
            reply_markup=main_menu_inline_keyboard(lang)
        )
    except Exception:
        await callback.message.answer(
            f"❌ <b>Qarz so'rovi bekor qilindi va o'chirildi.</b>\nMiqdor: {db.format_amount(debt['amount'])} {debt['currency']}",
            reply_markup=main_menu_keyboard(lang)
        )


@router.callback_query(F.data.startswith("debt_confirm_"))
async def confirm_debt(callback: CallbackQuery, bot: Bot) -> None:
    debt_id = callback.data.replace("debt_confirm_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "pending":
        await callback.answer(TEXTS[lang]["debt_not_found"], show_alert=True)
        return

    amount = debt["amount"]
    currency = debt["currency"]
    description = debt.get("description", "")
    desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""

    db.update_debt_status(debt_id, "active")

    other_id = debt["creditor_id"] if str(debt.get("debtor_id")) == str(user_id) else debt["debtor_id"]
    other_user = db.get_user(other_id) if other_id else None
    other_name = other_user["full_name"] if other_user else "N/A"

    await callback.message.edit_text(
        TEXTS[lang]["debt_confirmed_by_you"].format(
            name=other_name,
            amount=db.format_amount(amount),
            currency=currency,
            desc_line=desc_line,
        )
    )
    await callback.answer()

    if other_id:
        other_lang = db.get_user_language(other_id)
        confirmer = db.get_user(user_id)
        confirmer_name = confirmer["full_name"] if confirmer else "N/A"
        other_desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""
        try:
            await bot.send_message(
                int(other_id),
                TEXTS[other_lang]["debt_confirmed_by_other"].format(
                    name=confirmer_name,
                    amount=db.format_amount(amount),
                    currency=currency,
                    desc_line=other_desc_line,
                ),
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("debt_reject_"))
async def reject_debt(callback: CallbackQuery, bot: Bot) -> None:
    debt_id = callback.data.replace("debt_reject_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "pending":
        await callback.answer(TEXTS[lang]["debt_not_found"], show_alert=True)
        return

    amount = debt["amount"]
    currency = debt["currency"]
    description = debt.get("description", "")
    desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""

    db.update_debt_status(debt_id, "closed")

    other_id = debt["creditor_id"] if str(debt.get("debtor_id")) == str(user_id) else debt["debtor_id"]
    other_user = db.get_user(other_id) if other_id else None
    other_name = other_user["full_name"] if other_user else "N/A"

    await callback.message.edit_text(
        TEXTS[lang]["debt_rejected_by_you"].format(
            name=other_name,
            amount=db.format_amount(amount),
            currency=currency,
            desc_line=desc_line,
        )
    )
    await callback.answer()

    if other_id:
        other_lang = db.get_user_language(other_id)
        rejecter = db.get_user(user_id)
        rejecter_name = rejecter["full_name"] if rejecter else "N/A"
        other_desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""
        try:
            await bot.send_message(
                int(other_id),
                TEXTS[other_lang]["debt_rejected_by_other"].format(
                    name=rejecter_name,
                    amount=db.format_amount(amount),
                    currency=currency,
                    desc_line=other_desc_line,
                ),
            )
        except Exception:
            pass



