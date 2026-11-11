import logging

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import database as db
import keyboards as kb
from config import ADMIN_IDS
from utils import format_amount, format_datetime, validate_amount

logger = logging.getLogger(__name__)
router = Router(name="employee")


class EmployeeDebtStates(StatesGroup):
    choosing_currency = State()
    entering_amount = State()


def _is_employee_context(user_role: str) -> bool:
    return user_role == "employee"


# --------------------------------------------------------------------------- #
# BALANS
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_BALANCE, StateFilter("*"))
async def show_balance(message: Message, state: FSMContext) -> None:
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user is None:
        await message.answer("Foydalanuvchi topilmadi. /start ni bosing.")
        return
    text = (
        "💰 <b>Sizning balansingiz:</b>\n\n"
        f"So'mda: {format_amount(user.get('balance_uzs', 0), 'UZS')}\n"
        f"Dollarda: {format_amount(user.get('balance_usd', 0), 'USD')}"
    )
    await message.answer(text)


# --------------------------------------------------------------------------- #
# QARZ OLISH (increase, avtomatik)
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_TAKE_DEBT, StateFilter("*"))
async def take_debt_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(action="increase")
    await state.set_state(EmployeeDebtStates.choosing_currency)
    await message.answer("Qaysi valyutada qarz olmoqchisiz?", reply_markup=kb.currency_choice_kb())


# --------------------------------------------------------------------------- #
# QARZ TO'LASH (decrease, tasdiqlash talab qilinadi)
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_PAY_DEBT, StateFilter("*"))
async def pay_debt_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(action="decrease")
    await state.set_state(EmployeeDebtStates.choosing_currency)
    await message.answer(
        "Qaysi valyutada qarz to'lamoqchisiz?", reply_markup=kb.currency_choice_kb()
    )


@router.callback_query(
    F.data.startswith("curr:"), StateFilter(EmployeeDebtStates.choosing_currency)
)
async def employee_currency_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.split(":", 1)[1]
    await state.update_data(currency=currency)
    await state.set_state(EmployeeDebtStates.entering_amount)
    await callback.message.edit_text(f"Valyuta tanlandi: {currency}\nSummani kiriting:")
    await callback.answer()


@router.message(StateFilter(EmployeeDebtStates.entering_amount))
async def employee_amount_entered(message: Message, state: FSMContext, bot: Bot) -> None:
    amount = validate_amount(message.text)
    if amount is None:
        await message.answer(
            "❗ Noto'g'ri summa. Faqat musbat son kiriting (masalan: 150000 yoki 25.50)."
        )
        return

    data = await state.get_data()
    action = data["action"]
    currency = data["currency"]
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    full_name = user.get("full_name", str(user_id)) if user else str(user_id)

    await state.clear()

    if action == "increase":
        await db.update_balance(user_id, currency, amount)
        await db.add_transaction(
            user_id=user_id,
            tx_type="increase",
            currency=currency,
            amount=amount,
            status="completed",
            created_by="employee",
        )
        await message.answer(
            f"✅ Qarzingizga {format_amount(amount, currency)} qo'shildi.",
            reply_markup=kb.employee_main_menu(),
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"ℹ️ <b>{full_name}</b> {format_amount(amount, currency)} qarz oldi.",
                )
            except Exception:
                logger.exception("Adminga (%s) xabar yuborib bo'lmadi", admin_id)

    else:  # decrease -> tasdiqlash talab qilinadi
        tx_id = await db.add_transaction(
            user_id=user_id,
            tx_type="decrease",
            currency=currency,
            amount=amount,
            status="pending",
            created_by="employee",
        )
        await message.answer(
            "⏳ So'rovingiz adminga yuborildi. Tasdiqlanishini kuting.",
            reply_markup=kb.employee_main_menu(),
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    (
                        f"🔔 <b>{full_name}</b> {format_amount(amount, currency)} "
                        "to'lamoqchi. Tasdiqlaysizmi?"
                    ),
                    reply_markup=kb.approval_kb(tx_id),
                )
            except Exception:
                logger.exception("Adminga (%s) xabar yuborib bo'lmadi", admin_id)


# --------------------------------------------------------------------------- #
# TARIX
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_HISTORY, StateFilter("*"))
async def show_history(message: Message, state: FSMContext) -> None:
    await state.clear()
    transactions = await db.get_user_transactions(message.from_user.id, limit=20)
    if not transactions:
        await message.answer("Sizda hali qarz operatsiyalari yo'q.")
        return

    status_map = {"completed": "✅ Bajarildi", "pending": "⏳ Kutilmoqda", "rejected": "❌ Rad etildi"}
    type_map = {"increase": "➕ Qarz olindi", "decrease": "➖ Qarz to'landi"}

    lines = ["📋 <b>Qarzlar tarixi:</b>\n"]
    for tx in transactions:
        lines.append(
            f"{format_datetime(tx.get('timestamp'))} | "
            f"{type_map.get(tx.get('type'), tx.get('type'))} | "
            f"{format_amount(tx.get('amount', 0), tx.get('currency', ''))} | "
            f"{status_map.get(tx.get('status'), tx.get('status'))}"
        )
    await message.answer("\n".join(lines))


# --------------------------------------------------------------------------- #
# BEKOR QILISH
# --------------------------------------------------------------------------- #

@router.message(F.text == kb.BTN_CANCEL, StateFilter("*"))
async def cancel_fsm_reply(message: Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        return
    await state.clear()
    user = await db.get_user(message.from_user.id)
    is_admin = user is not None and user.get("role") == "admin"
    menu = kb.admin_main_menu() if is_admin else kb.employee_main_menu()
    await message.answer("Bekor qilindi.", reply_markup=menu)


@router.callback_query(F.data == "fsm_cancel", StateFilter("*"))
async def cancel_fsm_callback(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text("Bekor qilindi.")
    await callback.answer()
