from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# --------------------------------------------------------------------------- #
# REPLY MENYULAR
# --------------------------------------------------------------------------- #

BTN_BALANCE = "💳 Qarzlarim"
BTN_TAKE_DEBT = "➕ Qarz olish"
BTN_PAY_DEBT = "➖ Qarz to'lash"
BTN_HISTORY = "📋 Qarzlar tarixi"

BTN_ADMIN_EMPLOYEES = "👥 Xodimlar ro'yxati"
BTN_ADMIN_ADD_EMPLOYEE = "➕ Xodim qo'shish"
BTN_ADMIN_INCREASE = "⬆️ Qarz ko'paytirish"
BTN_ADMIN_DECREASE = "⬇️ Qarz kamaytirish"
BTN_ADMIN_HISTORY = "📋 Qarzlar tarixi (admin)"

BTN_CANCEL = "❌ Bekor qilish"


def employee_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_BALANCE)],
            [KeyboardButton(text=BTN_TAKE_DEBT), KeyboardButton(text=BTN_PAY_DEBT)],
            [KeyboardButton(text=BTN_HISTORY)],
        ],
        resize_keyboard=True,
    )


def admin_main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_ADMIN_EMPLOYEES), KeyboardButton(text=BTN_ADMIN_ADD_EMPLOYEE)],
            [KeyboardButton(text=BTN_ADMIN_INCREASE), KeyboardButton(text=BTN_ADMIN_DECREASE)],
            [KeyboardButton(text=BTN_ADMIN_HISTORY)],
        ],
        resize_keyboard=True,
    )


def cancel_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


# --------------------------------------------------------------------------- #
# INLINE MENYULAR
# --------------------------------------------------------------------------- #

def currency_choice_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 UZS", callback_data="curr:UZS"),
                InlineKeyboardButton(text="💵 USD", callback_data="curr:USD"),
            ],
            [InlineKeyboardButton(text=BTN_CANCEL, callback_data="fsm_cancel")],
        ]
    )


def employees_choice_kb(employees: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{emp['full_name']}",
                callback_data=f"pickemp:{emp['user_id']}",
            )
        ]
        for emp in employees
    ]
    rows.append([InlineKeyboardButton(text=BTN_CANCEL, callback_data="fsm_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def approval_kb(tx_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"appr:{tx_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"rej:{tx_id}"),
            ]
        ]
    )
