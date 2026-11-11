import database as db
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from locales.texts import TEXTS


def currency_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 UZS", callback_data="currency_UZS"),
                InlineKeyboardButton(text="💵 USD", callback_data="currency_USD"),
            ],
            [
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


def debt_confirm_keyboard(lang: str, debt_id: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t["btn_confirm"], callback_data=f"debt_confirm_{debt_id}"),
                InlineKeyboardButton(text=t["btn_reject"], callback_data=f"debt_reject_{debt_id}"),
            ]
        ]
    )


def payment_confirm_keyboard(lang: str, debt_id: str, amount: float) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t["btn_confirm"], callback_data=f"pay_confirm_{debt_id}_{amount}"
                ),
                InlineKeyboardButton(
                    text=t["btn_reject"], callback_data=f"pay_reject_{debt_id}_{amount}"
                ),
            ]
        ]
    )


def add_button_keyboard(lang: str, role: str, pending_debts: list = None) -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []
    if pending_debts:
        for p in pending_debts:
            btn_text = f"❌ Bekor qilish: {p['name']} ({db.format_amount(p['amount'])} {p['currency']})"
            rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"debt_cancel_creator_{p['debt_id']}")])
    rows.append([InlineKeyboardButton(text=t["btn_add_new"], callback_data=f"add_debt_{role}")])
    rows.append([InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def debts_interactive_keyboard(lang: str, role: str, active_debts: list = None, pending_debts: list = None) -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []
    if active_debts:
        for d in active_debts:
            name = d.get("name", "Noma'lum")
            amt = db.format_amount(d.get("amount", 0))
            curr = d.get("currency", "UZS")
            btn_text = f"👤 {name}: {amt} {curr}"
            rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"debt_view_{d['debt_id']}")])
            
    if pending_debts:
        for p in pending_debts:
            name = p.get("name", "Noma'lum")
            amt = db.format_amount(p.get("amount", 0))
            curr = p.get("currency", "UZS")
            btn_text = f"🟡 {name}: {amt} {curr} (kutilmoqda)"
            rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"debt_view_{p['debt_id']}")])
            
    rows.append([InlineKeyboardButton(text=t.get("btn_add_new", "➕ Yangi qo'shish"), callback_data=f"add_debt_{role}")])
    rows.append([InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def debt_actions_keyboard(debt_id: str, role: str, status: str, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []
    if status == "active":
        rows.append([
            InlineKeyboardButton(text="✅ Qarzni to'liq yopish", callback_data=f"debt_close_{debt_id}")
        ])
        rows.append([
            InlineKeyboardButton(text="💸 Qisman to'lash (kamaytirish)", callback_data=f"debt_part_{debt_id}")
        ])
        rows.append([
            InlineKeyboardButton(text="🔔 Eslatma yuborish", callback_data=f"debt_remind_{debt_id}")
        ])
    elif status == "pending":
        rows.append([
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"debt_cancel_creator_{debt_id}")
        ])
    elif status == "closed":
        rows.append([
            InlineKeyboardButton(text="🔄 Qayta faollashtirish", callback_data=f"debt_reopen_{debt_id}")
        ])
        
    back_target = "creditor" if role == "creditor" else "debtor"
    rows.append([
        InlineKeyboardButton(text="🔙 Ro'yxatga qaytish", callback_data=f"debt_back_{back_target}"),
        InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def person_list_keyboard(people: list, prefix: str, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []
    for p in people:
        label = f"{p['name']} ({db.format_amount(p['amount'])} {p['currency']})"
        rows.append([InlineKeyboardButton(text=label, callback_data=f"{prefix}_{p['debt_id']}")])
    rows.append([InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_menu_inline_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")]
        ]
    )


def broadcast_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    t = TEXTS[lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t["btn_confirm"], callback_data="broadcast_confirm"),
                InlineKeyboardButton(text=t["btn_reject"], callback_data="broadcast_cancel"),
            ]
        ]
    )


def share_debt_keyboard(link: str, text: str, phone: str = "", lang: str = "uz", debt_id: str = "") -> InlineKeyboardMarkup:
    import urllib.parse
    from config import SMS_WEB_URL
    t = TEXTS.get(lang, TEXTS["uz"])
    
    # Telegram ulashish
    encoded_text_tg = urllib.parse.quote_plus(text)
    share_url = f"https://t.me/share/url?url={urllib.parse.quote_plus(link)}&text={encoded_text_tg}"
    
    # SMS orqali ulashish (Veb sahifaga yo'naltirish)
    encoded_text_sms = urllib.parse.quote(text)
    encoded_phone = urllib.parse.quote(phone) if phone else ""
    base_web_url = SMS_WEB_URL.rstrip("/") + "/"
    sms_url = f"{base_web_url}?text={encoded_text_sms}&phone={encoded_phone}"

    buttons = [
        [InlineKeyboardButton(text="✈️ Telegramda ulashish", url=share_url)],
        [InlineKeyboardButton(text="📱 SMS orqali ulashish", url=sms_url)],
    ]

    if debt_id:
        buttons.append([InlineKeyboardButton(text=t.get("btn_cancel_pending", "❌ So'rovni bekor qilish"), callback_data=f"debt_cancel_creator_{debt_id}")])
    buttons.append([InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)



def settings_keyboard(lang: str = "uz", user_id: int = None) -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    buttons = [
        [InlineKeyboardButton(text=t.get("btn_invite_friends", "👥 Do'stlarga ulashish"), callback_data="invite_friends")],
        [InlineKeyboardButton(text=t["btn_change_language"], callback_data="settings_change_language")],
        [InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_change_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="set_lang_kk")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")],
        ]
    )


# ==================== SHAXSIY MOLIYA INLINE KEYBOARDS ====================

def finance_main_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t.get("fin_btn_income", "➕ Kirim"), callback_data="fin_add_income"),
                InlineKeyboardButton(text=t.get("fin_btn_expense", "➖ Chiqim"), callback_data="fin_add_expense"),
            ],
            [
                InlineKeyboardButton(text=t.get("fin_btn_balance", "💼 Balans"), callback_data="fin_view_balance_month"),
                InlineKeyboardButton(text=t.get("fin_btn_report", "📊 Hisobot"), callback_data="fin_view_report_month"),
            ],
            [
                InlineKeyboardButton(text=t.get("fin_btn_history", "📜 Xarajatlar tarixi"), callback_data="fin_view_history_0"),
            ],
            [
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


def finance_balance_period_keyboard(current_period: str = "month", view_type: str = "balance", lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    
    p_today = ("✅ " if current_period == "today" else "") + t.get("fin_period_today", "📅 Bugun")
    p_week = ("✅ " if current_period == "week" else "") + t.get("fin_period_week", "🗓 Bu hafta")
    p_month = ("✅ " if current_period == "month" else "") + t.get("fin_period_month", "📊 Bu oy")
    p_all = ("✅ " if current_period == "all" else "") + t.get("fin_period_all", "📈 Barchasi")

    prefix = f"fin_view_{view_type}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=p_today, callback_data=f"{prefix}_today"),
                InlineKeyboardButton(text=p_week, callback_data=f"{prefix}_week"),
            ],
            [
                InlineKeyboardButton(text=p_month, callback_data=f"{prefix}_month"),
                InlineKeyboardButton(text=p_all, callback_data=f"{prefix}_all"),
            ],
            [
                InlineKeyboardButton(text=t.get("fin_btn_income", "➕ Kirim"), callback_data="fin_add_income"),
                InlineKeyboardButton(text=t.get("fin_btn_expense", "➖ Chiqim"), callback_data="fin_add_expense"),
            ],
            [
                InlineKeyboardButton(text="💼 Moliya markazi", callback_data="to_finance_menu"),
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


def finance_category_keyboard(categories: list, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []
    current_row = []
    for idx, cat in enumerate(categories):
        current_row.append(InlineKeyboardButton(text=cat, callback_data=f"fincat_{idx}"))
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)

    rows.append([InlineKeyboardButton(text="✏️ Yangi kategoriya yozish", callback_data="fincat_custom")])
    rows.append([InlineKeyboardButton(text=t.get("btn_cancel", "❌ Bekor qilish"), callback_data="to_finance_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def finance_quick_confirm_keyboard(tx_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"fin_edit_{tx_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"fin_del_{tx_id}"),
            ],
            [
                InlineKeyboardButton(text="💼 Balansni ko'rish", callback_data="fin_view_balance_month"),
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


def finance_history_pagination_keyboard(page: int, total_pages: int, tx_list: list, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    rows = []

    # Individual transaction buttons to view / edit
    for idx, tx in enumerate(tx_list):
        sign = "➕" if tx.get("type") == "income" else "➖"
        btn_label = f"{idx + 1}. {sign} {db.format_amount(tx['amount'])} {tx['currency']} ({tx.get('category', '')[:12]})"
        rows.append([InlineKeyboardButton(text=btn_label, callback_data=f"fintx_detail_{tx['tx_id']}_{page}")])

    # Pagination navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"fin_view_history_{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page + 1}/{max(1, total_pages)}", callback_data="fin_noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"fin_view_history_{page + 1}"))

    if nav_row:
        rows.append(nav_row)

    rows.append([
        InlineKeyboardButton(text=t.get("fin_btn_income", "➕ Kirim"), callback_data="fin_add_income"),
        InlineKeyboardButton(text=t.get("fin_btn_expense", "➖ Chiqim"), callback_data="fin_add_expense"),
    ])
    rows.append([
        InlineKeyboardButton(text="💼 Moliya markazi", callback_data="to_finance_menu"),
        InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def finance_tx_action_keyboard(tx_id: str, page: int = 0, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"fin_edit_{tx_id}"),
                InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"fin_del_{tx_id}"),
            ],
            [
                InlineKeyboardButton(text="📜 Tarixga qaytish", callback_data=f"fin_view_history_{page}"),
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


def finance_tx_edit_keyboard(tx_id: str, lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Summa", callback_data=f"finedit_amount_{tx_id}"),
                InlineKeyboardButton(text="📂 Kategoriya", callback_data=f"finedit_cat_{tx_id}"),
            ],
            [
                InlineKeyboardButton(text="📝 Izoh", callback_data=f"finedit_note_{tx_id}"),
                InlineKeyboardButton(text="📅 Sana", callback_data=f"finedit_date_{tx_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"fintx_detail_{tx_id}_0"),
            ],
        ]
    )


# ==================== HISOBOTLAR MARKAZI (REPORTS HUB) ====================

def reports_hub_keyboard(active_tab: str = "all", period: str = "month", lang: str = "uz") -> InlineKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["uz"])

    tab_all = ("🔵 " if active_tab == "all" else "") + "🌐 Umumiy Jamlama"
    tab_fin = ("🔵 " if active_tab == "finance" else "") + "💼 Shaxsiy Moliya"
    tab_debts = ("🔵 " if active_tab == "debts" else "") + "🤝 Qarzlar Tahlili"

    p_today = ("✅ " if period == "today" else "") + "Bugun"
    p_week = ("✅ " if period == "week" else "") + "Hafta"
    p_month = ("✅ " if period == "month" else "") + "Bu oy"
    p_all = ("✅ " if period == "all" else "") + "Barchasi"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tab_all, callback_data=f"rep_tab_all_{period}"),
            ],
            [
                InlineKeyboardButton(text=tab_fin, callback_data=f"rep_tab_finance_{period}"),
                InlineKeyboardButton(text=tab_debts, callback_data=f"rep_tab_debts_{period}"),
            ],
            [
                InlineKeyboardButton(text=p_today, callback_data=f"rep_tab_{active_tab}_today"),
                InlineKeyboardButton(text=p_week, callback_data=f"rep_tab_{active_tab}_week"),
                InlineKeyboardButton(text=p_month, callback_data=f"rep_tab_{active_tab}_month"),
                InlineKeyboardButton(text=p_all, callback_data=f"rep_tab_{active_tab}_all"),
            ],
            [
                InlineKeyboardButton(text="💼 Moliya markazi", callback_data="to_finance_menu"),
                InlineKeyboardButton(text=t.get("btn_main_menu", "🏠 Asosiy menyu"), callback_data="to_main_menu"),
            ],
        ]
    )


