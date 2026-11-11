import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

import database as db
import keyboards as kb
from config import ADMIN_IDS
from utils import format_amount, format_datetime, validate_amount



logger = logging.getLogger(__name__)
router = Router(name="admin")

# Ushbu routerdagi barcha handlerlar faqat ADMIN_IDS ro'yxatidagi
# foydalanuvchilar uchun ishlaydi (xodim tugma matnini qo'lda yozib
# admin funksiyalariga kira olmasligi uchun).
router.message.filter(F.from_user.id.in_(ADMIN_IDS))
router.callback_query.filter(F.from_user.id.in_(ADMIN_IDS))


class AdminDebtStates(StatesGroup):
    choosing_employee = State()
    choosing_currency = State()
    entering_amount = State()


class AddEmployeeStates(StatesGroup):
    entering_id = State()
    entering_name = State()


# --------------------------------------------------------------------------- #
# XODIMLAR RO'YXATI
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_ADMIN_EMPLOYEES, StateFilter("*"))
async def list_employees(message: Message, state: FSMContext) -> None:
    await state.clear()
    employees = await db.get_all_employees()
    if not employees:
        await message.answer("Hozircha xodimlar ro'yxati bo'sh.")
        return

    lines = ["👥 <b>Xodimlar ro'yxati:</b>\n"]
    for emp in employees:
        lines.append(
            f"• <b>{emp['full_name']}</b> (ID: {emp['user_id']})\n"
            f"   So'm: {format_amount(emp.get('balance_uzs', 0), 'UZS')} | "
            f"Dollar: {format_amount(emp.get('balance_usd', 0), 'USD')}"
        )
    await message.answer("\n".join(lines))


# --------------------------------------------------------------------------- #
# XODIM QO'SHISH (admin tomonidan ID orqali)
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_ADMIN_ADD_EMPLOYEE, StateFilter("*"))
async def add_employee_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddEmployeeStates.entering_id)
    await message.answer(
        "➕ <b>Yangi xodim qo'shish</b>\n\n"
        "Xodimning Telegram <b>ID raqamini</b> kiriting:\n"
        "<i>(Xodim @userinfobot ga /start yozib o'z ID sini bilishi mumkin)</i>",
        reply_markup=kb.cancel_menu(),
    )


@router.message(StateFilter(AddEmployeeStates.entering_id))
async def add_employee_id_entered(message: Message, state: FSMContext) -> None:
    text = message.text.strip() if message.text else ""
    if not text.lstrip("-").isdigit():
        await message.answer("❗ Faqat son kiriting. Masalan: <code>522760123</code>")
        return
    user_id = int(text)
    existing = await db.get_user(user_id)
    if existing is not None:
        await state.clear()
        await message.answer(
            f"⚠️ Bu ID (<code>{user_id}</code>) allaqachon ro'yxatda bor: "
            f"<b>{existing['full_name']}</b>",
            reply_markup=kb.admin_main_menu(),
        )
        return
    await state.update_data(new_user_id=user_id)
    await state.set_state(AddEmployeeStates.entering_name)
    await message.answer(f"ID: <code>{user_id}</code>\n\nXodimning <b>to'liq ismini</b> kiriting:")


@router.message(StateFilter(AddEmployeeStates.entering_name))
async def add_employee_name_entered(message: Message, state: FSMContext) -> None:
    full_name = (message.text or "").strip()
    if not full_name:
        await message.answer("❗ Ism bo'sh bo'lmasligi kerak.")
        return
    data = await state.get_data()
    user_id = data["new_user_id"]
    await state.clear()
    await db.get_or_create_user(user_id, full_name, role="employee")
    await message.answer(
        f"✅ Xodim muvaffaqiyatli qo'shildi!\n\n"
        f"👤 <b>{full_name}</b>\n"
        f"🆔 <code>{user_id}</code>",
        reply_markup=kb.admin_main_menu(),
    )


# --------------------------------------------------------------------------- #
# QARZ KO'PAYTIRISH / KAMAYTIRISH (admin tomonidan, tasdiqlashsiz)
# --------------------------------------------------------------------------- #

@router.message(F.text.in_({kb.BTN_ADMIN_INCREASE, kb.BTN_ADMIN_DECREASE}), StateFilter("*"))
async def admin_debt_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    action = "increase" if message.text == kb.BTN_ADMIN_INCREASE else "decrease"
    employees = await db.get_all_employees()
    if not employees:
        await message.answer("Xodimlar ro'yxati bo'sh.")
        return

    await state.update_data(action=action)
    await state.set_state(AdminDebtStates.choosing_employee)
    await message.answer("Xodimni tanlang:", reply_markup=kb.employees_choice_kb(employees))


@router.callback_query(
    F.data.startswith("pickemp:"), StateFilter(AdminDebtStates.choosing_employee)
)
async def admin_employee_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    employee_id = int(callback.data.split(":", 1)[1])
    await state.update_data(employee_id=employee_id)
    await state.set_state(AdminDebtStates.choosing_currency)
    await callback.message.edit_text(
        "Valyutani tanlang:", reply_markup=kb.currency_choice_kb()
    )
    await callback.answer()


@router.callback_query(
    F.data.startswith("curr:"), StateFilter(AdminDebtStates.choosing_currency)
)
async def admin_currency_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.split(":", 1)[1]
    await state.update_data(currency=currency)
    await state.set_state(AdminDebtStates.entering_amount)
    await callback.message.edit_text(f"Valyuta: {currency}\nSummani kiriting:")
    await callback.answer()


@router.message(StateFilter(AdminDebtStates.entering_amount))
async def admin_amount_entered(message: Message, state: FSMContext, bot: Bot) -> None:
    amount = validate_amount(message.text)
    if amount is None:
        await message.answer(
            "❗ Noto'g'ri summa. Faqat musbat son kiriting (masalan: 150000 yoki 25.50)."
        )
        return

    data = await state.get_data()
    action = data["action"]
    currency = data["currency"]
    employee_id = data["employee_id"]

    employee = await db.get_user(employee_id)
    if employee is None:
        await state.clear()
        await message.answer("Xodim topilmadi.", reply_markup=kb.admin_main_menu())
        return

    await state.clear()

    delta = amount if action == "increase" else -amount
    await db.update_balance(employee_id, currency, delta)
    await db.add_transaction(
        user_id=employee_id,
        tx_type=action,
        currency=currency,
        amount=amount,
        status="completed",
        created_by="admin",
    )

    verb = "qo'shildi" if action == "increase" else "ayirildi"
    await message.answer(
        f"✅ <b>{employee['full_name']}</b> balansiga {format_amount(amount, currency)} {verb}.",
        reply_markup=kb.admin_main_menu(),
    )
    try:
        arrow = "➕" if action == "increase" else "➖"
        await bot.send_message(
            employee_id,
            f"{arrow} Balansingizga {format_amount(amount, currency)} {verb}.",
        )
    except Exception:
        logger.exception("Xodimga (%s) xabar yuborib bo'lmadi", employee_id)


# --------------------------------------------------------------------------- #
# TASDIQLASH OQIMI (xodim "Qarz to'lash" so'rovi uchun)
# --------------------------------------------------------------------------- #

@router.callback_query(F.data.startswith("appr:"))
async def approve_transaction(callback: CallbackQuery, bot: Bot) -> None:
    tx_id = callback.data.split(":", 1)[1]
    tx = await db.get_transaction(tx_id)

    if tx is None:
        await callback.answer("Tranzaksiya topilmadi.", show_alert=True)
        return
    if tx["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_balance(tx["user_id"], tx["currency"], -tx["amount"])
    await db.update_transaction_status(tx_id, "completed")

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Tasdiqlandi</b>", reply_markup=None
    )
    await callback.answer("Tasdiqlandi.")

    try:
        await bot.send_message(
            tx["user_id"],
            f"✅ {format_amount(tx['amount'], tx['currency'])} to'lovingiz tasdiqlandi.",
        )
    except Exception:
        logger.exception("Xodimga (%s) xabar yuborib bo'lmadi", tx["user_id"])


@router.callback_query(F.data.startswith("rej:"))
async def reject_transaction(callback: CallbackQuery, bot: Bot) -> None:
    tx_id = callback.data.split(":", 1)[1]
    tx = await db.get_transaction(tx_id)

    if tx is None:
        await callback.answer("Tranzaksiya topilmadi.", show_alert=True)
        return
    if tx["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_transaction_status(tx_id, "rejected")

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ <b>Rad etildi</b>", reply_markup=None
    )
    await callback.answer("Rad etildi.")

    try:
        await bot.send_message(
            tx["user_id"],
            f"❌ {format_amount(tx['amount'], tx['currency'])} to'lov so'rovingiz rad etildi.",
        )
    except Exception:
        logger.exception("Xodimga (%s) xabar yuborib bo'lmadi", tx["user_id"])


# --------------------------------------------------------------------------- #
# QARZLAR TARIXI — xodim tanlash va ko'rsatish
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_ADMIN_HISTORY, StateFilter("*"))
async def admin_history_choose(message: Message, state: FSMContext) -> None:
    await state.clear()
    employees = await db.get_all_employees()
    if not employees:
        await message.answer("Hozircha xodimlar ro'yxati bo'sh.")
        return

    rows = [
        [InlineKeyboardButton(
            text=f"👤 {emp['full_name']}",
            callback_data=f"hist:{emp['user_id']}",
        )]
        for emp in employees
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await message.answer("📋 <b>Qarzlar tarixi</b>\n\nXodimni tanlang:", reply_markup=markup)


@router.callback_query(F.data.startswith("hist:"))
async def admin_history_show(callback: CallbackQuery) -> None:
    user_id = int(callback.data.split(":", 1)[1])
    transactions = await db.get_user_transactions(user_id, limit=50)

    # Xodim ma'lumotlarini olish
    user = await db.get_user(user_id)
    name = user["full_name"] if user else str(user_id)

    await callback.answer()

    if not transactions:
        await callback.message.answer(f"👤 <b>{name}</b>\n\nHali hech qanday operatsiya yo'q.")
        return

    status_map = {"completed": "✅", "pending": "⏳", "rejected": "❌"}
    type_map   = {"increase": "➕ Qarz olindi", "decrease": "➖ To'lov"}

    lines = [f"📋 <b>{name} — qarz tarixi:</b>\n"]
    for tx in transactions:
        lines.append(
            f"🕐 {format_datetime(tx.get('timestamp'))}\n"
            f"   {type_map.get(tx.get('type'), tx.get('type'))} | "
            f"{format_amount(tx.get('amount', 0), tx.get('currency', ''))} | "
            f"{status_map.get(tx.get('status'), tx.get('status'))}"
        )

    # Jami qarzlar (bazadan hozirgi balans)
    uzs = user.get("balance_uzs", 0) if user else 0
    usd = user.get("balance_usd", 0) if user else 0
    lines.append(
        f"\n━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Jami qarz:</b>\n"
        f"   🇺🇿 So'mda:   <b>{format_amount(uzs, 'UZS')}</b>\n"
        f"   💵 Dollarda: <b>{format_amount(usd, 'USD')}</b>"
    )

    text = "\n".join(lines)
    for i in range(0, len(text), 4000):
        await callback.message.answer(text[i: i + 4000])
