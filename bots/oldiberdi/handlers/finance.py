import re
from datetime import datetime
from typing import Optional

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import database as db
from keyboards.default import (
    cancel_keyboard,
    finance_date_keyboard,
    main_menu_keyboard,
    skip_description_keyboard,
)
from keyboards.inline import (
    currency_keyboard,
    finance_balance_period_keyboard,
    finance_category_keyboard,
    finance_history_pagination_keyboard,
    finance_main_keyboard,
    finance_quick_confirm_keyboard,
    finance_tx_action_keyboard,
    finance_tx_edit_keyboard,
    main_menu_inline_keyboard,
    payment_confirm_keyboard,
    person_list_keyboard,
    reports_hub_keyboard,
)
from locales.texts import TEXTS
from states import AddPersonalFinance, EditPersonalFinance, FinanceOperation

router = Router(name="finance")

ALL_BTN_PERSONAL_FINANCE = [t.get("btn_personal_finance", "💼 Shaxsiy moliya") for t in TEXTS.values()] + [
    "Shaxsiy moliya", "Личные финансы", "Жеке қаржы", "Personal Finance", "/finance"
]
ALL_BTN_REPORTS = [t.get("btn_report", "📊 Hisobotlar") for t in TEXTS.values()] + [
    "Hisobotlar", "Отчеты", "Есептер", "Reports", "/report", "/reports", "Hisobot", "Отчет"
]
ALL_BTN_INCOME = [t.get("btn_income", "📥 Kirim") for t in TEXTS.values()]
ALL_BTN_OUTCOME = [t.get("btn_outcome", "📤 Chiqim") for t in TEXTS.values()]
ALL_BTN_CANCEL = [t.get("btn_cancel", "❌ Bekor qilish") for t in TEXTS.values()] + ["/cancel", "Bekor qilish", "Отмена"]
ALL_BTN_MAIN_MENU = [t.get("btn_main_menu", "🏠 Asosiy menyu") for t in TEXTS.values()] + [
    "/menu", "Asosiy menyu", "Главное меню", "Басты мәзір"
]
ALL_BTN_SKIP = [t.get("btn_skip", "➡️ O'tkazib yuborish") for t in TEXTS.values()] + [
    "/skip", "O'tkazib yuborish", "Пропустить", "Өткізіп жіберу"
]


def generate_report_text(user_id: int, active_tab: str = "all", period: str = "month") -> str:
    rep = db.get_comprehensive_financial_report(user_id, period=period)
    fin = rep["finance"]
    debts = rep["debts"]
    net = rep["net_worth"]

    period_names = {
        "today": "Bugun",
        "week": "Bu hafta",
        "month": "Bu oy",
        "all": "Barcha vaqt",
    }
    p_name = period_names.get(period, period)

    if active_tab == "all":
        uzs_w_sign = "+" if fin["UZS"]["balance"] > 0 else ""
        usd_w_sign = "+" if fin["USD"]["balance"] > 0 else ""

        uzs_nw_sign = "+" if net["UZS"] > 0 else ""
        usd_nw_sign = "+" if net["USD"] > 0 else ""

        lines = [
            f"📊 <b>Umumiy Moliyaviy Jamlama Hisoboti</b> ({p_name}):",
            "",
            "💼 <b>1. Shaxsiy Moliya (Kassa/Hamyon):</b>",
            f"  ➕ Jami kirim: <b>+{db.format_amount(fin['UZS']['income'])} UZS</b>",
            f"  ➖ Jami chiqim: <b>-{db.format_amount(fin['UZS']['expense'])} UZS</b>",
            f"  💰 Sof hamyon qoldig'i: <b>{uzs_w_sign}{db.format_amount(fin['UZS']['balance'])} UZS</b>",
        ]
        if fin["USD"]["income"] > 0 or fin["USD"]["expense"] > 0:
            lines.append(f"  💵 USD qoldiq: <b>{usd_w_sign}{db.format_amount(fin['USD']['balance'])} USD</b>")

        lines.extend([
            "",
            "🤝 <b>2. Qarzlar va Majburiyatlar:</b>",
            f"  📤 Men olishim kerak (Haqdorligim): <b>{db.format_amount(debts['lent']['uzs'])} UZS</b> ({debts['lent']['active_count']} ta faol)",
            f"  📥 Men berishim kerak (Qarzlarim): <b>{db.format_amount(debts['borrowed']['uzs'])} UZS</b> ({debts['borrowed']['active_count']} ta faol)",
            f"  ⚖️ Qarzlar sof saldosi: <b>{'+' if debts['net_uzs'] > 0 else ''}{db.format_amount(debts['net_uzs'])} UZS</b>",
        ])
        if debts["lent"]["usd"] > 0 or debts["borrowed"]["usd"] > 0:
            lines.append(f"  💵 USD qarzlar saldosi: <b>{'+' if debts['net_usd'] > 0 else ''}{db.format_amount(debts['net_usd'])} USD</b>")

        lines.extend([
            "",
            "💎 <b>3. Umumiy Sof Aktivlar (Net Worth):</b>",
            f"  🇺🇿 <b>{uzs_nw_sign}{db.format_amount(net['UZS'])} UZS</b>",
        ])
        if net["USD"] != 0:
            lines.append(f"  💵 <b>{usd_nw_sign}{db.format_amount(net['USD'])} USD</b>")

        lines.extend([
            "",
            "<i>(Sof aktiv = Hamyondagi pul + Men olishim kerak qarzlar - Men to'lashim kerak qarzlar)</i>"
        ])
        return "\n".join(lines)

    elif active_tab == "finance":
        uzs_exp = fin["UZS"]["expense"]
        cats_uzs = fin["UZS"]["categories"]
        max_exp = fin["UZS"]["max_expense"]

        lines = [
            f"💼 <b>Shaxsiy Moliya Hisoboti</b> ({p_name}):",
            f"➕ Kirim: <b>+{db.format_amount(fin['UZS']['income'])} UZS</b>",
            f"➖ Chiqim: <b>-{db.format_amount(uzs_exp)} UZS</b>",
            f"💰 Qoldiq: <b>{'+' if fin['UZS']['balance'] > 0 else ''}{db.format_amount(fin['UZS']['balance'])} UZS</b>",
            f"🔢 Tranzaksiyalar: <b>{fin['total_count']} ta</b>",
            "",
        ]
        if not cats_uzs:
            lines.append("<i>Bu davrda xarajatlar qayd etilmagan.</i>")
        else:
            lines.append("📂 <b>Xarajatlar taqsimoti:</b>")
            sorted_cats = sorted(cats_uzs.items(), key=lambda x: x[1], reverse=True)
            for cat, amt in sorted_cats:
                pct = int((amt / uzs_exp * 100)) if uzs_exp > 0 else 0
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                lines.append(f"• {cat}: <b>{db.format_amount(amt)} UZS</b> ({pct}%)\n  <code>{bar}</code>")

            if max_exp:
                n_str = f" ({max_exp['note']})" if max_exp.get("note") else ""
                lines.append("")
                lines.append(f"🔥 <b>Eng katta xarajat:</b> {db.format_amount(max_exp['amount'])} UZS{n_str} - {max_exp['date']}")

        return "\n".join(lines)

    elif active_tab == "debts":
        lines = [
            "🤝 <b>Qarzlar Tahlili va Hisoboti:</b>",
            "",
            "📤 <b>Men bergan qarzlar (Debtorlar):</b>",
            f"• Faol qarzlar soni: <b>{debts['lent']['active_count']} ta</b>",
            f"• Yopilgan qarzlar soni: <b>{debts['lent']['closed_count']} ta</b>",
            f"• Jami kutilayotgan summa: <b>{db.format_amount(debts['lent']['uzs'])} UZS</b>" + (f" | <b>{db.format_amount(debts['lent']['usd'])} USD</b>" if debts['lent']['usd'] > 0 else ""),
            "",
            "📥 <b>Men olgan qarzlar (Kreditorlar):</b>",
            f"• Faol qarzlar soni: <b>{debts['borrowed']['active_count']} ta</b>",
            f"• To'lab yopilgan qarzlar: <b>{debts['borrowed']['closed_count']} ta</b>",
            f"• Jami to'lanishi kerak: <b>{db.format_amount(debts['borrowed']['uzs'])} UZS</b>" + (f" | <b>{db.format_amount(debts['borrowed']['usd'])} USD</b>" if debts['borrowed']['usd'] > 0 else ""),
            "",
        ]

        if debts["lent"]["top_items"]:
            lines.append("📋 <b>Eng katta qarzdorlar (Kimdan qancha kutilmoqda):</b>")
            for idx, d in enumerate(debts["lent"]["top_items"], 1):
                p_name = db.get_debt_party_name(d, user_id)
                due = f" (Muddat: {d['due_date']})" if d.get("due_date") else ""
                lines.append(f"{idx}. <b>{p_name}</b>: {db.format_amount(d['amount'])} {d['currency']}{due}")
            lines.append("")

        if debts["borrowed"]["top_items"]:
            lines.append("📋 <b>Eng katta haqdorlar (Kimga qancha berish kerak):</b>")
            for idx, d in enumerate(debts["borrowed"]["top_items"], 1):
                p_name = db.get_debt_party_name(d, user_id)
                due = f" (Muddat: {d['due_date']})" if d.get("due_date") else ""
                lines.append(f"{idx}. <b>{p_name}</b>: {db.format_amount(d['amount'])} {d['currency']}{due}")

        return "\n".join(lines)

    return "Hisobot mavjud emas."



# ==================== SHAXSIY MOLIYA ASOSIY MENYU ====================

@router.message(F.text.in_(ALL_BTN_PERSONAL_FINANCE))
async def show_personal_finance(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bal = db.get_finance_balance(user_id, period="month")
    uzs_bal = bal["UZS"]["balance"]
    usd_bal = bal["USD"]["balance"]

    uzs_sign = "+" if uzs_bal > 0 else ""
    usd_sign = "+" if usd_bal > 0 else ""

    summary_text = (
        f"{t.get('fin_main_menu', '💼 <b>Shaxsiy Moliya Markazi</b>')}\n\n"
        f"📊 <b>Bu oydagi holat:</b>\n"
        f"🇺🇿 UZS: <b>{uzs_sign}{db.format_amount(uzs_bal)} UZS</b> (Kirim: +{db.format_amount(bal['UZS']['income'])}, Chiqim: -{db.format_amount(bal['UZS']['expense'])})\n"
        f"💵 USD: <b>{usd_sign}{db.format_amount(usd_bal)} USD</b>\n\n"
        f"Tranzaksiyalar: {bal['total_count']} ta"
    )

    await message.answer(summary_text, reply_markup=finance_main_keyboard(lang))


@router.callback_query(F.data == "to_finance_menu")
async def callback_to_finance_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bal = db.get_finance_balance(user_id, period="month")
    uzs_bal = bal["UZS"]["balance"]
    usd_bal = bal["USD"]["balance"]

    uzs_sign = "+" if uzs_bal > 0 else ""
    usd_sign = "+" if usd_bal > 0 else ""

    summary_text = (
        f"{t.get('fin_main_menu', '💼 <b>Shaxsiy Moliya Markazi</b>')}\n\n"
        f"📊 <b>Bu oydagi holat:</b>\n"
        f"🇺🇿 UZS: <b>{uzs_sign}{db.format_amount(uzs_bal)} UZS</b> (Kirim: +{db.format_amount(bal['UZS']['income'])}, Chiqim: -{db.format_amount(bal['UZS']['expense'])})\n"
        f"💵 USD: <b>{usd_sign}{db.format_amount(usd_bal)} USD</b>\n\n"
        f"Tranzaksiyalar: {bal['total_count']} ta"
    )

    try:
        await callback.message.edit_text(summary_text, reply_markup=finance_main_keyboard(lang))
    except Exception:
        await callback.message.answer(summary_text, reply_markup=finance_main_keyboard(lang))
    await callback.answer()


# ==================== HISOBOTLAR MARKAZI (REPORTS HUB) ====================

@router.message(F.text.in_(ALL_BTN_REPORTS))
async def show_reports_hub(message: Message, state: FSMContext) -> None:
    await state.clear()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    rep_text = generate_report_text(user_id, active_tab="all", period="month")
    await message.answer(rep_text, reply_markup=reports_hub_keyboard(active_tab="all", period="month", lang=lang))


@router.callback_query(F.data.startswith("rep_tab_"))
async def callback_reports_tab(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    # rep_tab_{tab}_{period}
    active_tab = parts[2]
    period = parts[3] if len(parts) > 3 else "month"

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    rep_text = generate_report_text(user_id, active_tab=active_tab, period=period)
    try:
        await callback.message.edit_text(
            rep_text, reply_markup=reports_hub_keyboard(active_tab=active_tab, period=period, lang=lang)
        )
    except Exception:
        await callback.message.answer(
            rep_text, reply_markup=reports_hub_keyboard(active_tab=active_tab, period=period, lang=lang)
        )
    await callback.answer()


# ==================== BALANS KO'RISH ====================

@router.callback_query(F.data.startswith("fin_view_balance_"))
async def view_finance_balance(callback: CallbackQuery) -> None:
    period = callback.data.replace("fin_view_balance_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bal = db.get_finance_balance(user_id, period=period)
    
    period_names = {
        "today": t.get("fin_period_today", "Bugun"),
        "week": t.get("fin_period_week", "Bu hafta"),
        "month": t.get("fin_period_month", "Bu oy"),
        "all": t.get("fin_period_all", "Barcha vaqt"),
    }
    p_name = period_names.get(period, period)

    uzs_inc = bal["UZS"]["income"]
    uzs_exp = bal["UZS"]["expense"]
    uzs_rem = bal["UZS"]["balance"]
    uzs_sign = "+" if uzs_rem > 0 else ""

    usd_inc = bal["USD"]["income"]
    usd_exp = bal["USD"]["expense"]
    usd_rem = bal["USD"]["balance"]
    usd_sign = "+" if usd_rem > 0 else ""

    text = (
        f"💼 <b>Shaxsiy Moliya Balansi</b> ({p_name}):\n\n"
        f"🇺🇿 <b>UZS:</b>\n"
        f"  ➕ Kirim: <b>+{db.format_amount(uzs_inc)} UZS</b>\n"
        f"  ➖ Chiqim: <b>-{db.format_amount(uzs_exp)} UZS</b>\n"
        f"  💰 Sof qoldiq: <b>{uzs_sign}{db.format_amount(uzs_rem)} UZS</b>\n\n"
        f"💵 <b>USD:</b>\n"
        f"  ➕ Kirim: <b>+{db.format_amount(usd_inc)} USD</b>\n"
        f"  ➖ Chiqim: <b>-{db.format_amount(usd_exp)} USD</b>\n"
        f"  💰 Sof qoldiq: <b>{usd_sign}{db.format_amount(usd_rem)} USD</b>\n\n"
        f"🔢 Jami amallar: <b>{bal['total_count']} ta</b>"
    )

    try:
        await callback.message.edit_text(
            text, reply_markup=finance_balance_period_keyboard(period, "balance", lang)
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=finance_balance_period_keyboard(period, "balance", lang)
        )
    await callback.answer()


# ==================== HISOBOT (REPORT) ====================

@router.callback_query(F.data.startswith("fin_view_report_"))
async def view_finance_report(callback: CallbackQuery) -> None:
    period = callback.data.replace("fin_view_report_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    bal = db.get_finance_balance(user_id, period=period)
    
    period_names = {
        "today": t.get("fin_period_today", "Bugun"),
        "week": t.get("fin_period_week", "Bu hafta"),
        "month": t.get("fin_period_month", "Bu oy"),
        "all": t.get("fin_period_all", "Barcha vaqt"),
    }
    p_name = period_names.get(period, period)

    uzs_exp = bal["UZS"]["expense"]
    cats_uzs = bal["UZS"]["categories"]
    max_exp_uzs = bal["UZS"]["max_expense"]

    lines = [
        f"📊 <b>Xarajatlar hisoboti</b> ({p_name}):",
        f"💰 Jami chiqim: <b>{db.format_amount(uzs_exp)} UZS</b>",
        "",
    ]

    if not cats_uzs:
        lines.append("<i>Bu davrda xarajatlar qayd etilmagan.</i>")
    else:
        lines.append("📂 <b>Kategoriyalar bo'yicha taqsimot:</b>")
        sorted_cats = sorted(cats_uzs.items(), key=lambda x: x[1], reverse=True)
        for cat, amt in sorted_cats:
            pct = int((amt / uzs_exp * 100)) if uzs_exp > 0 else 0
            filled_blocks = int(pct / 10)
            bar = "█" * filled_blocks + "░" * (10 - filled_blocks)
            lines.append(f"• {cat}: <b>{db.format_amount(amt)} UZS</b> ({pct}%)\n  <code>{bar}</code>")

        if max_exp_uzs:
            note_str = f" ({max_exp_uzs['note']})" if max_exp_uzs.get("note") else ""
            lines.append("")
            lines.append(
                f"🔥 <b>Eng katta xarajat:</b> {db.format_amount(max_exp_uzs['amount'])} UZS{note_str} - {max_exp_uzs['date']}"
            )

    # USD if exists
    if bal["USD"]["expense"] > 0:
        lines.append("")
        lines.append(f"💵 <b>USD xarajatlar:</b> {db.format_amount(bal['USD']['expense'])} USD")
        for cat, amt in bal["USD"]["categories"].items():
            lines.append(f"• {cat}: {db.format_amount(amt)} USD")

    try:
        await callback.message.edit_text(
            "\n".join(lines), reply_markup=finance_balance_period_keyboard(period, "report", lang)
        )
    except Exception:
        await callback.message.answer(
            "\n".join(lines), reply_markup=finance_balance_period_keyboard(period, "report", lang)
        )
    await callback.answer()


# ==================== XARAJATLAR TARIXI ====================

@router.callback_query(F.data.startswith("fin_view_history_"))
async def view_finance_history(callback: CallbackQuery) -> None:
    page_str = callback.data.replace("fin_view_history_", "", 1)
    page = int(page_str) if page_str.isdigit() else 0
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    txs = db.get_user_finance_transactions(user_id, period="all")
    if not txs:
        empty_text = "📜 <b>Xarajat va daromadlar tarixi bo'sh.</b>\n\nQuyidagi tugmalar orqali birinchi yozuvingizni kiriting 👇"
        try:
            await callback.message.edit_text(empty_text, reply_markup=finance_main_keyboard(lang))
        except Exception:
            await callback.message.answer(empty_text, reply_markup=finance_main_keyboard(lang))
        await callback.answer()
        return

    page_size = 5
    total_pages = (len(txs) + page_size - 1) // page_size
    page = max(0, min(page, total_pages - 1))

    start_idx = page * page_size
    page_txs = txs[start_idx : start_idx + page_size]

    lines = [
        f"📜 <b>Xarajat va kirimlar tarixi</b> (Sahifa {page + 1}/{total_pages}):",
        "",
    ]

    for idx, tx in enumerate(page_txs, 1):
        sign = "➕" if tx.get("type") == "income" else "➖"
        note = f" — <i>{tx['note']}</i>" if tx.get("note") else ""
        lines.append(
            f"<b>{idx}.</b> {sign} <b>{db.format_amount(tx['amount'])} {tx['currency']}</b> | {tx.get('category', '📦 Boshqa')}\n"
            f"   📅 {tx.get('date', '')}{note}"
        )

    lines.append("")
    lines.append("<i>Tranzaksiyani tahrirlash yoki o'chirish uchun quyidagi tugmalardan birini tanlang:</i>")

    try:
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=finance_history_pagination_keyboard(page, total_pages, page_txs, lang),
        )
    except Exception:
        await callback.message.answer(
            "\n".join(lines),
            reply_markup=finance_history_pagination_keyboard(page, total_pages, page_txs, lang),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("fintx_detail_"))
async def view_tx_detail(callback: CallbackQuery) -> None:
    parts = callback.data.split("_")
    tx_id = parts[2]
    page = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0

    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    tx = db.get_finance_transaction(tx_id)
    if not tx:
        await callback.answer("Tranzaksiya topilmadi!", show_alert=True)
        return

    sign = "➕ Kirim" if tx.get("type") == "income" else "➖ Chiqim"
    note = tx.get("note") or "Mavjud emas"

    text = (
        f"📄 <b>Tranzaksiya tafsilotlari:</b>\n\n"
        f"Turi: <b>{sign}</b>\n"
        f"Summa: <b>{db.format_amount(tx['amount'])} {tx['currency']}</b>\n"
        f"Kategoriya: <b>{tx.get('category', '📦 Boshqa')}</b>\n"
        f"Izoh: <i>{note}</i>\n"
        f"Sana: <b>{tx.get('date', '')}</b>\n"
    )

    await callback.message.edit_text(text, reply_markup=finance_tx_action_keyboard(tx_id, page, lang))
    await callback.answer()


@router.callback_query(F.data.startswith("fin_del_"))
async def delete_tx_handler(callback: CallbackQuery) -> None:
    tx_id = callback.data.replace("fin_del_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    db.delete_finance_transaction(tx_id)
    await callback.answer(TEXTS[lang].get("fin_deleted_success", "Tranzaksiya o'chirildi!"), show_alert=True)
    await view_finance_history(callback)


@router.callback_query(F.data.startswith("fin_edit_"))
async def edit_tx_start(callback: CallbackQuery) -> None:
    tx_id = callback.data.replace("fin_edit_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    tx = db.get_finance_transaction(tx_id)
    if not tx:
        await callback.answer("Tranzaksiya topilmadi!", show_alert=True)
        return

    text = (
        f"✏️ <b>Tranzaksiyani tahrirlash:</b>\n\n"
        f"Joriy summa: <b>{db.format_amount(tx['amount'])} {tx['currency']}</b>\n"
        f"Kategoriya: <b>{tx.get('category', '📦 Boshqa')}</b>\n"
        f"Izoh: <i>{tx.get('note', '')}</i>\n"
        f"Sana: <b>{tx.get('date', '')}</b>\n\n"
        f"Qaysi ma'lumotni o'zgartirmoqchisiz?"
    )

    await callback.message.edit_text(text, reply_markup=finance_tx_edit_keyboard(tx_id, lang))
    await callback.answer()


# ==================== TAHRIRLASH (EDITING) ====================

@router.callback_query(F.data.startswith("finedit_amount_"))
async def edit_amount_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    tx_id = callback.data.replace("finedit_amount_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.set_state(EditPersonalFinance.editing_amount)
    await state.update_data(edit_tx_id=tx_id)
    await callback.message.answer("💰 <b>Yangi summani kiriting:</b> (masalan: 75 000 yoki 100k)", reply_markup=cancel_keyboard(lang))
    await callback.answer()


@router.message(EditPersonalFinance.editing_amount, F.text)
async def process_edit_amount(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    data = await state.get_data()
    tx_id = data["edit_tx_id"]
    amount = db.parse_amount(message.text)
    if not amount or amount <= 0:
        await message.answer("Noto'g'ri summa! Musbat son kiriting:", reply_markup=cancel_keyboard(lang))
        return

    db.update_finance_transaction(tx_id, amount=amount)
    await state.clear()
    await message.answer(f"✅ Summa muvaffaqiyatli yangilandi: <b>{db.format_amount(amount)}</b>", reply_markup=main_menu_keyboard(lang))
    await message.answer("Quyidagi menyu orqali davom eting:", reply_markup=finance_main_keyboard(lang))


@router.callback_query(F.data.startswith("finedit_cat_"))
async def edit_cat_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    tx_id = callback.data.replace("finedit_cat_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.set_state(EditPersonalFinance.editing_category)
    await state.update_data(edit_tx_id=tx_id)
    cats = db.get_default_categories()
    await callback.message.answer("📂 <b>Yangi kategoriyani tanlang:</b>", reply_markup=finance_category_keyboard(cats, lang))
    await callback.answer()


def _resolve_category(raw_val: str) -> str:
    if raw_val == "custom":
        return "custom"
    cats = db.get_default_categories()
    if raw_val.isdigit():
        idx = int(raw_val)
        if 0 <= idx < len(cats):
            return cats[idx]
    return raw_val


@router.callback_query(EditPersonalFinance.editing_category, F.data.startswith("fincat_"))
async def process_edit_cat(callback: CallbackQuery, state: FSMContext) -> None:
    raw_val = callback.data.replace("fincat_", "", 1)
    cat_val = _resolve_category(raw_val)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    data = await state.get_data()
    tx_id = data.get("edit_tx_id")

    if cat_val == "custom":
        await state.set_state(EditPersonalFinance.editing_custom_category)
        await callback.message.answer("✏️ Yangi kategoriya nomini yozib yuboring:", reply_markup=cancel_keyboard(lang))
        await callback.answer()
        return

    if tx_id:
        db.update_finance_transaction(tx_id, category=cat_val)
        await state.clear()
        await callback.message.answer(f"✅ Kategoriya yangilandi: <b>{cat_val}</b>", reply_markup=main_menu_keyboard(lang))
        await callback.message.answer("Moliya markazi:", reply_markup=finance_main_keyboard(lang))
    await callback.answer()


@router.message(EditPersonalFinance.editing_custom_category, F.text)
async def process_edit_custom_cat(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    data = await state.get_data()
    tx_id = data["edit_tx_id"]
    new_cat = message.text.strip()
    db.update_finance_transaction(tx_id, category=new_cat)
    await state.clear()
    await message.answer(f"✅ Kategoriya yangilandi: <b>{new_cat}</b>", reply_markup=main_menu_keyboard(lang))
    await message.answer("Moliya markazi:", reply_markup=finance_main_keyboard(lang))


@router.callback_query(F.data.startswith("finedit_note_"))
async def edit_note_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    tx_id = callback.data.replace("finedit_note_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.set_state(EditPersonalFinance.editing_note)
    await state.update_data(edit_tx_id=tx_id)
    await callback.message.answer("📝 <b>Yangi izohni kiriting:</b>", reply_markup=skip_description_keyboard(lang))
    await callback.answer()


@router.message(EditPersonalFinance.editing_note, F.text)
async def process_edit_note(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    data = await state.get_data()
    tx_id = data["edit_tx_id"]
    note = "" if message.text in ALL_BTN_SKIP else message.text.strip()
    note_text = note or "(bo'sh)"
    await message.answer(f"✅ Izoh yangilandi: <i>{note_text}</i>", reply_markup=main_menu_keyboard(lang))
    await message.answer("Moliya markazi:", reply_markup=finance_main_keyboard(lang))


@router.callback_query(F.data.startswith("finedit_date_"))
async def edit_date_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    tx_id = callback.data.replace("finedit_date_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.set_state(EditPersonalFinance.editing_date)
    await state.update_data(edit_tx_id=tx_id)
    await callback.message.answer("📅 <b>Sanani tanlang yoki KK.OO.YYYY ko'rinishida yozing:</b>", reply_markup=finance_date_keyboard(lang))
    await callback.answer()


@router.message(EditPersonalFinance.editing_date, F.text)
async def process_edit_date(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    data = await state.get_data()
    tx_id = data["edit_tx_id"]

    date_val = message.text.strip()
    now_t = datetime.now(db.TASHKENT_TZ)
    if date_val in ["📅 Bugun", "Bugun", "Сегодня", "Бүгін", "Today"]:
        final_date = now_t.strftime("%d.%m.%Y")
    elif date_val in ["📅 Kecha", "Kecha", "Вчера", "Кеше", "Yesterday"]:
        from datetime import timedelta
        final_date = (now_t - timedelta(days=1)).strftime("%d.%m.%Y")
    else:
        final_date = db.format_date(date_val)

    db.update_finance_transaction(tx_id, date=final_date)
    await state.clear()
    await message.answer(f"✅ Sana yangilandi: <b>{final_date}</b>", reply_markup=main_menu_keyboard(lang))
    await message.answer("Moliya markazi:", reply_markup=finance_main_keyboard(lang))


# ==================== QADAM-BA-QADAM QO'SHISH (STEP-BY-STEP ADD) ====================

@router.callback_query(F.data.in_(["fin_add_income", "fin_add_expense"]))
async def start_add_finance_flow(callback: CallbackQuery, state: FSMContext) -> None:
    tx_type = "income" if callback.data == "fin_add_income" else "expense"
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    await state.set_state(AddPersonalFinance.entering_amount)
    await state.update_data(tx_type=tx_type)

    type_text = "Kirim" if tx_type == "income" else "Chiqim"
    prompt = t.get("fin_enter_amount", "💰 Summani kiriting:").format(type_text=type_text)

    await callback.message.answer(prompt, reply_markup=cancel_keyboard(lang))
    await callback.answer()


@router.message(AddPersonalFinance.entering_amount, F.text)
async def process_add_amount(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    amount = db.parse_amount(message.text)
    if not amount or amount <= 0:
        await message.answer(TEXTS[lang]["invalid_amount"], reply_markup=cancel_keyboard(lang))
        return

    await state.update_data(amount=amount)
    await state.set_state(AddPersonalFinance.choosing_currency)
    await message.answer("💵 <b>Valyutani tanlang:</b>", reply_markup=currency_keyboard(lang))


@router.callback_query(AddPersonalFinance.choosing_currency, F.data.startswith("currency_"))
async def process_add_currency(callback: CallbackQuery, state: FSMContext) -> None:
    currency = callback.data.replace("currency_", "", 1)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    await state.update_data(currency=currency)
    await state.set_state(AddPersonalFinance.choosing_category)

    cats = db.get_default_categories()
    await callback.message.answer("📂 <b>Kategoriyani tanlang:</b>", reply_markup=finance_category_keyboard(cats, lang))
    await callback.answer()


@router.callback_query(AddPersonalFinance.choosing_category, F.data.startswith("fincat_"))
async def process_add_category(callback: CallbackQuery, state: FSMContext) -> None:
    raw_val = callback.data.replace("fincat_", "", 1)
    cat_val = _resolve_category(raw_val)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    if cat_val == "custom":
        await state.set_state(AddPersonalFinance.entering_custom_category)
        await callback.message.answer("✏️ <b>Kategoriya nomini yozing:</b>", reply_markup=cancel_keyboard(lang))
        await callback.answer()
        return

    await state.update_data(category=cat_val)
    await state.set_state(AddPersonalFinance.entering_note)
    await callback.message.answer("📝 <b>Izoh kiriting (ixtiyoriy):</b>\n<i>Masalan: benzin, bozorlik...</i>", reply_markup=skip_description_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("fincat_"))
async def process_stale_category(callback: CallbackQuery) -> None:
    await callback.answer("Bu tugma eskirgan. Iltimos, «➕ Kirim» yoki «➖ Chiqim» tugmasini qayta bosing.", show_alert=True)


@router.message(AddPersonalFinance.entering_custom_category, F.text)
async def process_add_custom_category(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    custom_cat = message.text.strip()
    await state.update_data(category=custom_cat)
    await state.set_state(AddPersonalFinance.entering_note)
    await message.answer("📝 <b>Izoh kiriting (ixtiyoriy):</b>\n<i>Masalan: benzin, bozorlik...</i>", reply_markup=skip_description_keyboard(lang))


@router.message(AddPersonalFinance.entering_note, F.text)
async def process_add_note(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    note = "" if message.text in ALL_BTN_SKIP else message.text.strip()
    await state.update_data(note=note)
    await state.set_state(AddPersonalFinance.entering_date)
    await message.answer("📅 <b>Sanani tanlang yoki KK.OO.YYYY ko'rinishida yozing:</b>", reply_markup=finance_date_keyboard(lang))


@router.message(AddPersonalFinance.entering_date, F.text)
async def process_add_date(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)
    t = TEXTS.get(lang, TEXTS["uz"])

    if message.text in ALL_BTN_MAIN_MENU or message.text in ALL_BTN_CANCEL:
        await state.clear()
        await message.answer(TEXTS[lang]["cancelled"], reply_markup=main_menu_keyboard(lang))
        return

    data = await state.get_data()
    await state.clear()

    date_raw = message.text.strip()
    now_t = datetime.now(db.TASHKENT_TZ)
    if date_raw in ["📅 Bugun", "Bugun", "Сегодня", "Бүгін", "Today"]:
        final_date = now_t.strftime("%d.%m.%Y")
    elif date_raw in ["📅 Kecha", "Kecha", "Вчера", "Кеше", "Yesterday"]:
        from datetime import timedelta
        final_date = (now_t - timedelta(days=1)).strftime("%d.%m.%Y")
    else:
        final_date = db.format_date(date_raw)

    tx_type = data["tx_type"]
    amount = data["amount"]
    currency = data.get("currency", "UZS")
    category = data.get("category", "📦 Boshqa")
    note = data.get("note", "")

    tx_id = db.add_finance_transaction(
        user_id=user_id,
        type_=tx_type,
        amount=amount,
        currency=currency,
        category=category,
        note=note,
        date_str=final_date,
    )

    type_title = "Kirim" if tx_type == "income" else "Chiqim"
    sign = "➕" if tx_type == "income" else "➖"

    note_text = note if note else "(yo'q)"
    msg_text = (
        f"✅ <b>{type_title} muvaffaqiyatli saqlandi!</b>\n\n"
        f"{sign} <b>{db.format_amount(amount)} {currency}</b>\n"
        f"📂 Kategoriya: <b>{category}</b>\n"
        f"📝 Izoh: <i>{note_text}</i>\n"
        f"📅 Sana: <b>{final_date}</b>"
    )

    await message.answer(msg_text, reply_markup=main_menu_keyboard(lang))
    await message.answer("Tezkor amallar:", reply_markup=finance_quick_confirm_keyboard(tx_id, lang))


# ==================== TEZ KIRITISH (QUICK INPUT PARSER) ====================

@router.message(StateFilter(None), F.text)
async def handle_quick_finance_text(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    user_id = message.from_user.id
    lang = db.get_user_language(user_id)

    # If it matches quick finance syntax (e.g. -50k taksi, +5mln oylik, 120 000 bozor)
    parsed = db.parse_quick_finance(text)
    if parsed:
        tx_id = db.add_finance_transaction(
            user_id=user_id,
            type_=parsed["type"],
            amount=parsed["amount"],
            currency=parsed["currency"],
            category=parsed["category"],
            note=parsed["note"],
            date_str=parsed["date"],
        )

        type_title = "Kirim" if parsed["type"] == "income" else "Chiqim"
        sign = "➕" if parsed["type"] == "income" else "➖"

        parsed_note_text = parsed["note"] if parsed["note"] else "(yo'q)"
        msg_text = (
            f"⚡️ <b>{type_title} tezkor saqlandi!</b>\n\n"
            f"{sign} <b>{db.format_amount(parsed['amount'])} {parsed['currency']}</b>\n"
            f"📂 Kategoriya: <b>{parsed['category']}</b>\n"
            f"📝 Izoh: <i>{parsed_note_text}</i>\n"
            f"📅 Sana: <b>{parsed['date']}</b>"
        )

        await message.answer(msg_text, reply_markup=finance_quick_confirm_keyboard(tx_id, lang))
        return


# ==================== ESKI QARZ TO'LOVI FUNKSIYALARI (DEBT REPAYMENT) ====================

@router.callback_query(F.data.startswith("pay_confirm_"))
async def confirm_payment(callback: CallbackQuery, bot: Bot) -> None:
    _, _, debt_id, amount_str = callback.data.split("_", 3)
    amount = float(amount_str)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt or debt.get("status") != "active":
        await callback.answer(TEXTS[lang]["debt_not_found"], show_alert=True)
        return

    payer_id = debt["debtor_id"]
    receiver_id = debt["creditor_id"]
    old_total = debt["amount"]
    new_amount = round(old_total - amount, 2)
    description = debt.get("description", "")
    desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""

    if new_amount <= 0:
        db.update_debt_amount(debt_id, 0)
        db.update_debt_status(debt_id, "closed")
    else:
        db.update_debt_amount(debt_id, new_amount)

    db.add_history(debt_id, payer_id, receiver_id, "outcome", amount, debt["currency"], status="confirmed")

    status_line = (
        TEXTS[lang]["debt_fully_closed"] + "\n"
        if new_amount <= 0
        else TEXTS[lang]["debt_partially_closed"].format(remaining=db.format_amount(new_amount), currency=debt["currency"]) + "\n"
    )

    other_id = payer_id if str(user_id) == str(receiver_id) else receiver_id
    other_user = db.get_user(other_id)
    other_name = other_user["full_name"] if other_user else "N/A"

    await callback.message.edit_text(
        TEXTS[lang]["payment_confirmed_by_you"].format(
            name=other_name,
            amount=db.format_amount(amount),
            currency=debt["currency"],
            total=old_total,
            desc_line=desc_line,
            status_line=status_line,
        )
    )
    await callback.answer()

    other_lang = db.get_user_language(other_id)
    confirmer = db.get_user(user_id)
    confirmer_name = confirmer["full_name"] if confirmer else "N/A"
    other_desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""
    other_status_line = (
        TEXTS[other_lang]["debt_fully_closed"] + "\n"
        if new_amount <= 0
        else TEXTS[other_lang]["debt_partially_closed"].format(remaining=db.format_amount(new_amount), currency=debt["currency"]) + "\n"
    )

    try:
        await bot.send_message(
            int(other_id),
            TEXTS[other_lang]["payment_confirmed_by_other"].format(
                name=confirmer_name,
                amount=db.format_amount(amount),
                currency=debt["currency"],
                total=old_total,
                desc_line=other_desc_line,
                status_line=other_status_line,
            ),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("pay_reject_"))
async def reject_payment(callback: CallbackQuery, bot: Bot) -> None:
    _, _, debt_id, amount_str = callback.data.split("_", 3)
    amount = float(amount_str)
    user_id = callback.from_user.id
    lang = db.get_user_language(user_id)

    debt = db.get_debt(debt_id)
    if not debt:
        await callback.answer(TEXTS[lang]["debt_not_found"], show_alert=True)
        return

    total = debt["amount"]
    description = debt.get("description", "")
    desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""

    other_id = debt["debtor_id"] if str(user_id) == str(debt["creditor_id"]) else debt["creditor_id"]
    other_user = db.get_user(other_id)
    other_name = other_user["full_name"] if other_user else "N/A"

    await callback.message.edit_text(
        TEXTS[lang]["payment_rejected_by_you"].format(
            name=other_name,
            amount=db.format_amount(amount),
            currency=debt["currency"],
            total=db.format_amount(total),
            desc_line=desc_line,
        )
    )
    await callback.answer()

    other_lang = db.get_user_language(other_id)
    rejecter = db.get_user(user_id)
    rejecter_name = rejecter["full_name"] if rejecter else "N/A"
    other_desc_line = f"📝 Izoh: <b>{description}</b>\n" if description else ""

    try:
        await bot.send_message(
            int(other_id),
            TEXTS[other_lang]["payment_rejected_by_other"].format(
                name=rejecter_name,
                amount=db.format_amount(amount),
                currency=debt["currency"],
                total=db.format_amount(total),
                desc_line=other_desc_line,
            ),
        )
    except Exception:
        pass
