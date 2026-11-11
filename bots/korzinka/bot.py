import asyncio
import logging
import os
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

import config
from pdf_generator import create_akt_pdf, format_money

logging.basicConfig(level=logging.INFO)

router = Router()

import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_PATH = os.path.join(os.path.dirname(__file__), "acts.db")


# ---------------------------------------------------------------------------
# Ma'lumotlar bazasi — har bir akt uchun avtomatik raqam beradi
# ---------------------------------------------------------------------------
def init_db():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS acts (
                id SERIAL PRIMARY KEY,
                kod TEXT,
                manzil TEXT,
                sana TEXT,
                jami INTEGER,
                created_at TEXT,
                paid INTEGER DEFAULT 0,
                rasxod INTEGER DEFAULT 0,
                client_name TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS kirimlar (
                id SERIAL PRIMARY KEY,
                summa INTEGER NOT NULL,
                izoh TEXT DEFAULT '',
                sana TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
        # Add migrations just in case
        for col, col_type in [("paid", "INTEGER DEFAULT 0"), ("rasxod", "INTEGER DEFAULT 0"), ("client_name", "TEXT")]:
            try:
                cur.execute(f"ALTER TABLE acts ADD COLUMN {col} {col_type}")
                conn.commit()
            except Exception:
                conn.rollback()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS acts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kod TEXT,
                manzil TEXT,
                sana TEXT,
                jami INTEGER,
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS kirimlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summa INTEGER NOT NULL,
                izoh TEXT DEFAULT '',
                sana TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
        for migration in [
            "ALTER TABLE acts ADD COLUMN paid INTEGER DEFAULT 0",
            "ALTER TABLE acts ADD COLUMN rasxod INTEGER DEFAULT 0",
            "ALTER TABLE acts ADD COLUMN client_name TEXT",
        ]:
            try:
                conn.execute(migration)
                conn.commit()
            except Exception:
                pass
        conn.close()


def save_act_and_get_number(kod: str, manzil: str, sana: str, jami: int, client_name: str = None, rasxod: int = 0) -> str:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO acts (kod, manzil, sana, jami, client_name, rasxod, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (kod, manzil, sana, jami, client_name or config.CLIENT_NAME, rasxod, datetime.now().isoformat()),
        )
        act_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute(
            "INSERT INTO acts (kod, manzil, sana, jami, client_name, rasxod, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (kod, manzil, sana, jami, client_name or config.CLIENT_NAME, rasxod, datetime.now().isoformat()),
        )
        conn.commit()
        act_id = cur.lastrowid
        conn.close()
    return f"{act_id:04d}"


def get_hisobot_summary() -> dict:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*), COALESCE(SUM(jami), 0), "
            "COALESCE(SUM(CASE WHEN paid=1 THEN jami ELSE 0 END), 0), "
            "COALESCE(SUM(rasxod), 0) FROM acts"
        )
        row = cur.fetchone()
        cur.execute("SELECT COALESCE(SUM(summa), 0) FROM kirimlar")
        kirim_total = cur.fetchone()[0]
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(jami), 0), "
            "COALESCE(SUM(CASE WHEN paid=1 THEN jami ELSE 0 END), 0), "
            "COALESCE(SUM(rasxod), 0) FROM acts"
        ).fetchone()
        kirim_total = conn.execute(
            "SELECT COALESCE(SUM(summa), 0) FROM kirimlar"
        ).fetchone()[0]
        conn.close()
        
    total = row[1]
    rasxod = row[3]
    qarz = total - kirim_total
    foyda = total - rasxod
    return {
        "count": row[0],
        "total": total,
        "kirim": kirim_total,
        "qarz": qarz,
        "rasxod": rasxod,
        "foyda": foyda,
    }


ACTS_PER_PAGE = 5


def get_acts_page(page: int):
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        offset = page * ACTS_PER_PAGE
        cur.execute(
            "SELECT id, kod, manzil, sana, jami, paid, rasxod, client_name "
            "FROM acts ORDER BY id DESC LIMIT %s OFFSET %s",
            (ACTS_PER_PAGE, offset),
        )
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM acts")
        total = cur.fetchone()[0]
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        offset = page * ACTS_PER_PAGE
        rows = conn.execute(
            "SELECT id, kod, manzil, sana, jami, paid, rasxod, client_name "
            "FROM acts ORDER BY id DESC LIMIT ? OFFSET ?",
            (ACTS_PER_PAGE, offset),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM acts").fetchone()[0]
        conn.close()
    return rows, total


def toggle_act_paid(act_id: int):
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE acts SET paid = 1 - paid WHERE id = %s", (act_id,))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE acts SET paid = 1 - paid WHERE id = ?", (act_id,))
        conn.commit()
        conn.close()


def update_act_rasxod(act_id: int, rasxod: int):
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE acts SET rasxod = %s WHERE id = %s", (rasxod, act_id))
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE acts SET rasxod = ? WHERE id = ?", (rasxod, act_id))
        conn.commit()
        conn.close()


def add_kirim(summa: int, izoh: str, sana: str):
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO kirimlar (summa, izoh, sana, created_at) VALUES (%s, %s, %s, %s)",
            (summa, izoh, sana, datetime.now().isoformat()),
        )
        conn.commit()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO kirimlar (summa, izoh, sana, created_at) VALUES (?, ?, ?, ?)",
            (summa, izoh, sana, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()


def get_kirimlar_list() -> list:
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT summa, izoh, sana FROM kirimlar ORDER BY id DESC LIMIT 10"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT summa, izoh, sana FROM kirimlar ORDER BY id DESC LIMIT 10"
        ).fetchall()
        conn.close()
    return rows


# ---------------------------------------------------------------------------
# Oylik hisobot yordamchi funksiyalari
# ---------------------------------------------------------------------------
MONTH_NAMES = {
    "01": "Yanvar",
    "02": "Fevral",
    "03": "Mart",
    "04": "Aprel",
    "05": "May",
    "06": "Iyun",
    "07": "Iyul",
    "08": "Avgust",
    "09": "Sentyabr",
    "10": "Oktabr",
    "11": "Noyabr",
    "12": "Dekabr",
}


def format_month_name(month_str: str) -> str:
    parts = month_str.split(".")
    if len(parts) == 2:
        m, y = parts[0], parts[1]
        name = MONTH_NAMES.get(m, m)
        return f"{name} {y}"
    return month_str


def get_available_months() -> list[str]:
    months = set()
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT sana FROM acts WHERE sana IS NOT NULL")
        for row in cur.fetchall():
            sana = row[0]
            if sana and "." in sana:
                parts = sana.split(".")
                if len(parts) == 3:
                    months.add(f"{parts[1]}.{parts[2]}")
        cur.execute("SELECT sana FROM kirimlar WHERE sana IS NOT NULL")
        for row in cur.fetchall():
            sana = row[0]
            if sana and "." in sana:
                parts = sana.split(".")
                if len(parts) == 3:
                    months.add(f"{parts[1]}.{parts[2]}")
        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        for row in conn.execute("SELECT sana FROM acts WHERE sana IS NOT NULL").fetchall():
            sana = row[0]
            if sana and "." in sana:
                parts = sana.split(".")
                if len(parts) == 3:
                    months.add(f"{parts[1]}.{parts[2]}")
        for row in conn.execute("SELECT sana FROM kirimlar WHERE sana IS NOT NULL").fetchall():
            sana = row[0]
            if sana and "." in sana:
                parts = sana.split(".")
                if len(parts) == 3:
                    months.add(f"{parts[1]}.{parts[2]}")
        conn.close()

    current_month = datetime.now().strftime("%m.%Y")
    months.add(current_month)

    def month_key(m_str):
        p = m_str.split(".")
        return (int(p[1]), int(p[0])) if len(p) == 2 else (0, 0)

    return sorted(list(months), key=month_key, reverse=True)


def get_monthly_summary(month_str: str) -> dict:
    like_pattern = f"%.{month_str}"
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*), COALESCE(SUM(jami), 0), COALESCE(SUM(rasxod), 0) "
            "FROM acts WHERE sana LIKE %s",
            (like_pattern,)
        )
        row = cur.fetchone()
        count = row[0]
        total = row[1]
        rasxod = row[2]

        cur.execute(
            "SELECT COALESCE(SUM(summa), 0) FROM kirimlar WHERE sana LIKE %s",
            (like_pattern,)
        )
        kirim_total = cur.fetchone()[0]

        cur.execute(
            "SELECT id, kod, manzil, sana, jami, paid, rasxod, client_name "
            "FROM acts WHERE sana LIKE %s ORDER BY id ASC",
            (like_pattern,)
        )
        acts = cur.fetchall()

        cur.execute(
            "SELECT summa, izoh, sana FROM kirimlar WHERE sana LIKE %s ORDER BY id ASC",
            (like_pattern,)
        )
        kirimlar = cur.fetchall()

        cur.close()
        conn.close()
    else:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(jami), 0), COALESCE(SUM(rasxod), 0) "
            "FROM acts WHERE sana LIKE ?",
            (like_pattern,)
        ).fetchone()
        count = row[0]
        total = row[1]
        rasxod = row[2]

        kirim_total = conn.execute(
            "SELECT COALESCE(SUM(summa), 0) FROM kirimlar WHERE sana LIKE ?",
            (like_pattern,)
        ).fetchone()[0]

        acts = conn.execute(
            "SELECT id, kod, manzil, sana, jami, paid, rasxod, client_name "
            "FROM acts WHERE sana LIKE ? ORDER BY id ASC",
            (like_pattern,)
        ).fetchall()

        kirimlar = conn.execute(
            "SELECT summa, izoh, sana FROM kirimlar WHERE sana LIKE ? ORDER BY id ASC",
            (like_pattern,)
        ).fetchall()

        conn.close()

    foyda = total - rasxod
    qarz = total - kirim_total

    return {
        "month": month_str,
        "count": count,
        "total": total,
        "rasxod": rasxod,
        "foyda": foyda,
        "kirim": kirim_total,
        "qarz": qarz,
        "acts": acts,
        "kirimlar": kirimlar,
    }


def build_monthly_hisobot_message(month_str: str) -> tuple[str, InlineKeyboardMarkup]:
    months = get_available_months()
    if month_str not in months:
        month_str = months[0]

    summary = get_monthly_summary(month_str)
    month_name = format_month_name(month_str)

    acts_list_text = ""
    if summary["acts"]:
        acts_list_text = "\n📋 <b>Ochilgan marketlar / Aktlar:</b>\n"
        for i, (act_id, kod, manzil, sana, jami, paid, rasxod, client_name) in enumerate(summary["acts"], 1):
            client_display = f" · {client_name}" if client_name and client_name != config.CLIENT_NAME else ""
            kod_display = f" · {kod}" if kod else ""
            manzil_display = f" ({manzil})" if manzil else ""
            act_foyda = jami - (rasxod or 0)
            status_icon = "✅" if paid else "❌"

            acts_list_text += (
                f"{i}. {status_icon} <b>№{act_id:04d}</b> · {sana}{kod_display}{manzil_display}{client_display}\n"
                f"   🧾 Summa: <b>{format_money(jami)}</b> | 💸 Xarajat: <b>{format_money(rasxod or 0)}</b> | ✨ Foyda: <b>{format_money(act_foyda)}</b>\n"
            )
    else:
        acts_list_text = "\n<i>Ushbu oyda hech qanday akt kiritilmagan.</i>\n"

    kirim_lines = ""
    if summary["kirimlar"]:
        kirim_lines = "\n💵 <b>Ushbu oydagi to'lovlar (kirim):</b>\n"
        for summa, izoh, sana in summary["kirimlar"]:
            izoh_text = f" ({izoh})" if izoh else ""
            kirim_lines += f"  • {sana}: {format_money(summa)}{izoh_text}\n"

    text = (
        f"📅 <b>OYLIK HISOBOT: {month_name.upper()}</b>\n\n"
        f"🏪 Ochilgan marketlar soni: <b>{summary['count']} ta</b>\n"
        f"🧾 Jami xizmat summasi: <b>{format_money(summary['total'])}</b>\n"
        f"💸 Jami xarajat (Tan narxi): <b>{format_money(summary['rasxod'])}</b>\n"
        f"✨ <b>SOF FOYDA: {format_money(summary['foyda'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Korzinkadan tushgan pul: <b>{format_money(summary['kirim'])}</b>\n"
        f"🔴 Korzinka qarzi (qoldiq): <b>{format_money(summary['qarz'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━"
        f"{acts_list_text}"
        f"{kirim_lines}\n"
    )

    rows = []
    month_idx = months.index(month_str)
    nav_row = []
    if month_idx < len(months) - 1:
        prev_m = months[month_idx + 1]
        nav_row.append(InlineKeyboardButton(text=f"◀️ {format_month_name(prev_m)}", callback_data=f"mhisobot:{prev_m}"))
    if month_idx > 0:
        next_m = months[month_idx - 1]
        nav_row.append(InlineKeyboardButton(text=f"{format_month_name(next_m)} ▶️", callback_data=f"mhisobot:{next_m}"))

    if nav_row:
        rows.append(nav_row)

    m_buttons = []
    for m in months[:4]:
        is_curr = "🔘 " if m == month_str else ""
        m_buttons.append(InlineKeyboardButton(text=f"{is_curr}{format_month_name(m)}", callback_data=f"mhisobot:{m}"))
    if m_buttons:
        for i in range(0, len(m_buttons), 2):
            rows.append(m_buttons[i:i+2])

    rows.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"mhisobot:{month_str}")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------------------
# Holatlar (FSM)
# ---------------------------------------------------------------------------
class OrderForm(StatesGroup):
    kod = State()
    manzil = State()
    menu = State()
    waiting_value = State()


class AdminForm(StatesGroup):
    kirim_summa = State()
    kirim_izoh = State()
    smeta_summa = State()


class CustomOrderForm(StatesGroup):
    client_name = State()
    kod = State()
    manzil = State()
    item_name = State()
    item_qty = State()
    item_price = State()
    menu = State()


# ---------------------------------------------------------------------------
# Xizmatlar konfiguratsiyasi
# ---------------------------------------------------------------------------
SERVICES = {
    "shar_arka": {
        "label": "🎈 Shar (arka)",
        "type": "qty",
        "unit": "metr",
        "unit_price": config.PRICES["shar_arka_per_metr"],
        "cost_price": config.COST_PRICES["shar_arka_per_metr"],
        "ask_text": "Nechi metr? (faqat raqam yozing, masalan: 15)",
    },
    "shar_logo": {
        "label": "🎈 Shar (logotip)",
        "type": "qty",
        "unit": "dona",
        "unit_price": config.PRICES["shar_logo_per_dona"],
        "cost_price": config.COST_PRICES["shar_logo_per_dona"],
        "ask_text": "Nechta dona? (faqat raqam yozing, masalan: 100)",
    },
    "dj": {
        "label": "🎧 DJ",
        "type": "fixed",
        "price": config.PRICES["dj"],
        "cost_price": config.COST_PRICES["dj"],
    },
    "animator": {
        "label": "🤡 Animator",
        "type": "qty",
        "unit": "dona",
        "unit_price": config.PRICES["animator_per_dona"],
        "cost_price": config.COST_PRICES["animator_per_dona"],
        "ask_text": "Nechta animator? (faqat raqam yozing)",
    },
    "boshlovchi": {
        "label": "🎤 Boshlovchi",
        "type": "fixed",
        "price": config.PRICES["boshlovchi"],
        "cost_price": config.COST_PRICES["boshlovchi"],
    },
    "transport": {
        "label": "🚚 Transport",
        "type": "qty",
        "unit": "km",
        "unit_price": config.PRICES["transport_per_km"],
        "cost_price": config.COST_PRICES["transport_fixed"],
        "ask_text": "Nechi km? (faqat raqam yozing)",
    },
    "raqqosa": {
        "label": "💃 Raqqosa",
        "type": "qty",
        "unit": "dona",
        "unit_price": config.PRICES["raqqosa_per_dona"],
        "cost_price": config.COST_PRICES["raqqosa_per_dona"],
        "ask_text": "Nechta raqqosa? (faqat raqam yozing)",
    },
}

KARNAY_LABEL = "📯 Karnay-surnay"
KARNAY_PRICES = {"Shahar": config.PRICES["karnay_shahar"], "Viloyat": config.PRICES["karnay_viloyat"]}
KARNAY_COSTS = {"Shahar": config.COST_PRICES["karnay_shahar"], "Viloyat": config.COST_PRICES["karnay_viloyat"]}


def menu_header(data: dict) -> str:
    return f"Do'kon: {data['kod']}, {data['manzil']}\n\nKo'rsatilgan xizmatlarni belgilang:"


def build_main_menu(services: dict) -> InlineKeyboardMarkup:
    rows = []

    if "karnay" in services:
        text = f"✅ {KARNAY_LABEL} ({services['karnay']['label']})"
    else:
        text = KARNAY_LABEL
    rows.append([InlineKeyboardButton(text=text, callback_data="open:karnay")])

    for key, s in SERVICES.items():
        if s["type"] == "fixed":
            selected = key in services
            text = f"✅ {s['label']}" if selected else s["label"]
            rows.append([InlineKeyboardButton(text=text, callback_data=f"toggle:{key}")])
        else:
            if key in services:
                text = f"✅ {s['label']} ({services[key]['qty']:g} {s['unit']})"
            else:
                text = s["label"]
            rows.append([InlineKeyboardButton(text=text, callback_data=f"open:{key}")])

    jami = sum(v["total"] for v in services.values())
    rows.append([InlineKeyboardButton(text=f"💰 Jami: {format_money(jami)}", callback_data="noop")])
    rows.append([InlineKeyboardButton(text="✅ Tayyor — Akt yaratish", callback_data="done")])
    rows.append([InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_order")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_karnay_menu(services: dict) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"🏙 Shahar — {format_money(KARNAY_PRICES['Shahar'])}",
            callback_data="karnay:Shahar",
        )],
        [InlineKeyboardButton(
            text=f"🌍 Viloyat — {format_money(KARNAY_PRICES['Viloyat'])}",
            callback_data="karnay:Viloyat",
        )],
    ]
    if "karnay" in services:
        rows.append([InlineKeyboardButton(text="🗑 Olib tashlash", callback_data="karnay:remove")])
    rows.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="karnay:back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


NEW_ORDER_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Yangi akt"), KeyboardButton(text="✍️ Erkin akt")]
    ],
    resize_keyboard=True,
)

ADMIN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Yangi akt"), KeyboardButton(text="✍️ Erkin akt")],
        [KeyboardButton(text="📊 Hisobot"), KeyboardButton(text="📅 Oylik hisobot")],
        [KeyboardButton(text="💵 Kirim kiritish")],
    ],
    resize_keyboard=True,
)


def get_main_kb(user_id: int) -> ReplyKeyboardMarkup:
    return ADMIN_KB if user_id in config.ADMIN_IDS else NEW_ORDER_KB


def build_hisobot_message(page: int) -> tuple[str, InlineKeyboardMarkup]:
    acts, total_count = get_acts_page(page)
    s = get_hisobot_summary()
    total_pages = max((total_count + ACTS_PER_PAGE - 1) // ACTS_PER_PAGE, 1)

    # Kirimlar ro'yxati
    kirimlar = get_kirimlar_list()
    kirim_lines = ""
    if kirimlar:
        kirim_lines = "\n\n💵 <b>So'nggi kirimlar:</b>\n"
        for summa, izoh, sana in kirimlar[:5]:
            izoh_text = f" ({izoh})" if izoh else ""
            kirim_lines += f"  • {sana}: {format_money(summa)}{izoh_text}\n"

    text = (
        f"📊 <b>HISOBOT</b>\n\n"
        f"📋 Jami aktlar: <b>{s['count']} ta</b>\n"
        f"🧾 Aktlar summasi: <b>{format_money(s['total'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Korzinkadan keldi: <b>{format_money(s['kirim'])}</b>\n"
        f"🔴 Korzinka qarzi: <b>{format_money(s['qarz'])}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 Umumiy rasxod: <b>{format_money(s['rasxod'])}</b>\n"
        f"✨ Sof foyda: <b>{format_money(s['foyda'])}</b>\n"
        f"{kirim_lines}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"<i>Sahifa {page + 1}/{total_pages}</i>"
    )

    rows = []
    for act_id, kod, _manzil, sana, jami, paid, rasxod, client_name in acts:
        # 1-qator: to'lov holati (toggle)
        icon = "✅" if paid else "❌"
        client_display = f" · {client_name}" if client_name and client_name != config.CLIENT_NAME else ""
        kod_display = f" · {kod}" if kod else ""
        label = f"{icon} №{act_id:04d} · {sana}{kod_display}{client_display} · {format_money(jami)}"
        rows.append([InlineKeyboardButton(
            text=label,
            callback_data=f"paid_toggle:{act_id}:{page}",
        )])
        # 2-qator: smeta / rasxod
        if rasxod:
            foyda_act = jami - rasxod
            foyda_sign = "+" if foyda_act >= 0 else ""
            smeta_label = (
                f"📝 Rasxod: {format_money(rasxod)} "
                f"| Foyda: {foyda_sign}{format_money(foyda_act)}"
            )
        else:
            smeta_label = "📝 Smeta kiritilmagan — bosib kiriting"
        rows.append([InlineKeyboardButton(
            text=smeta_label,
            callback_data=f"smeta_open:{act_id}:{page}",
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀ Oldingi", callback_data=f"hisobot_page:{page - 1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="Keyingi ▶", callback_data=f"hisobot_page:{page + 1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"hisobot_page:{page}")])

    return text, InlineKeyboardMarkup(inline_keyboard=rows)


# ---------------------------------------------------------------------------
# Handlerlar
# ---------------------------------------------------------------------------
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum!\n\n"
        "Bu bot ochilish kunida bajarilgan ishlar bo'yicha akt (PDF) tayyorlab beradi.\n\n"
        "Yangi akt boshlash uchun pastdagi tugmani bosing.",
        reply_markup=get_main_kb(message.from_user.id),
    )


@router.message(F.text == "🆕 Yangi akt")
async def new_order(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderForm.kod)
    await message.answer("Do'kon kodini yozing (masalan: K-234):")


@router.message(OrderForm.kod)
async def get_kod(message: Message, state: FSMContext):
    await state.update_data(kod=message.text.strip())
    await state.set_state(OrderForm.manzil)
    await message.answer("Manzilini yozing (masalan: Shahrisabz):")


@router.message(OrderForm.manzil)
async def get_manzil(message: Message, state: FSMContext):
    await state.update_data(manzil=message.text.strip(), services={})
    await state.set_state(OrderForm.menu)
    data = await state.get_data()
    await message.answer(menu_header(data), reply_markup=build_main_menu({}))


@router.callback_query(OrderForm.menu, F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(OrderForm.menu, F.data == "open:karnay")
async def open_karnay(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await callback.message.edit_text(
        "Karnay-surnay uchun hududni tanlang:",
        reply_markup=build_karnay_menu(data.get("services", {})),
    )
    await callback.answer()


@router.callback_query(OrderForm.menu, F.data.startswith("karnay:"))
async def karnay_choice(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    services = data.get("services", {})

    if action in KARNAY_PRICES:
        services["karnay"] = {
            "label": action,
            "qty": 1,
            "total": KARNAY_PRICES[action],
            "cost_total": KARNAY_COSTS[action],
        }
    elif action == "remove":
        services.pop("karnay", None)
    # "back" — o'zgarishsiz asosiy menyuga qaytadi

    await state.update_data(services=services)
    await callback.message.edit_text(menu_header(data), reply_markup=build_main_menu(services))
    await callback.answer()


@router.callback_query(OrderForm.menu, F.data.startswith("toggle:"))
async def toggle_fixed(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    data = await state.get_data()
    services = data.get("services", {})

    if key in services:
        services.pop(key)
    else:
        s = SERVICES[key]
        services[key] = {
            "qty": 1,
            "total": s["price"],
            "cost_total": s["cost_price"],
        }

    await state.update_data(services=services)
    await callback.message.edit_text(menu_header(data), reply_markup=build_main_menu(services))
    await callback.answer()


@router.callback_query(OrderForm.menu, F.data.startswith("open:"))
async def open_qty_service(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":", 1)[1]
    if key not in SERVICES or SERVICES[key]["type"] != "qty":
        await callback.answer()
        return

    await state.update_data(pending_service=key)
    await state.set_state(OrderForm.waiting_value)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="cancel_ask")]]
    )
    await callback.message.edit_text(SERVICES[key]["ask_text"], reply_markup=kb)
    await callback.answer()


@router.callback_query(OrderForm.waiting_value, F.data == "cancel_ask")
async def cancel_ask(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await state.set_state(OrderForm.menu)
    await callback.message.edit_text(menu_header(data), reply_markup=build_main_menu(data.get("services", {})))
    await callback.answer()


@router.message(OrderForm.waiting_value)
async def get_qty_value(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        qty = float(text)
        if qty <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Iltimos, musbat raqam kiriting (masalan: 15).")
        return

    data = await state.get_data()
    key = data["pending_service"]
    s = SERVICES[key]
    services = data.get("services", {})
    cost_total = s["cost_price"] if key == "transport" else qty * s["cost_price"]
    services[key] = {
        "qty": qty,
        "unit": s["unit"],
        "total": qty * s["unit_price"],
        "cost_total": cost_total,
    }
    await state.update_data(services=services, pending_service=None)
    await state.set_state(OrderForm.menu)

    await message.answer(menu_header(data), reply_markup=build_main_menu(services))


@router.callback_query(OrderForm.menu, F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Akt bekor qilindi.")
    await callback.message.answer("Yangi akt boshlash uchun tugmani bosing.", reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


@router.callback_query(OrderForm.menu, F.data == "done")
async def finish_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    services = data.get("services", {})

    if not services:
        await callback.answer("Hech qanday xizmat tanlanmadi!", show_alert=True)
        return

    kod = data["kod"]
    manzil = data["manzil"]
    sana = datetime.now().strftime("%d.%m.%Y")
    jami = sum(v["total"] for v in services.values())
    rasxod = sum(v.get("cost_total", 0) for v in services.values())

    akt_raqami = save_act_and_get_number(kod, manzil, sana, int(jami), client_name=config.CLIENT_NAME, rasxod=int(rasxod))

    items = []
    if "karnay" in services:
        v = services["karnay"]
        items.append(("Karnay-surnay", v["label"], format_money(v["total"]), v["total"]))
    for key, s in SERVICES.items():
        if key in services:
            v = services[key]
            name = s["label"].split(" ", 1)[1]
            if s["type"] == "fixed":
                items.append((name, "1 xizmat", format_money(v["total"]), v["total"]))
            else:
                items.append((name, f"{v['qty']:g} {v['unit']}", format_money(v["total"]), v["total"]))

    pdf_path = create_akt_pdf(
        akt_raqami=akt_raqami,
        kod=kod,
        manzil=manzil,
        sana=sana,
        items=items,
        jami=jami,
    )

    await callback.message.edit_text(f"✅ Akt №{akt_raqami} tayyor. Jami: {format_money(jami)}")
    await callback.message.answer_document(
        FSInputFile(pdf_path), caption=f"Akt №{akt_raqami} — {kod}, {manzil}"
    )
    await state.clear()
    await callback.message.answer("Yangi akt boshlash uchun tugmani bosing.", reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


@router.message(F.text == "📊 Hisobot")
async def show_hisobot(message: Message):
    if not config.ADMIN_IDS or message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ Sizda ushbu bo'limga kirish huquqi yo'q.")
        return
    text, kb = build_hisobot_message(page=0)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "📅 Oylik hisobot")
async def show_monthly_hisobot(message: Message):
    if not config.ADMIN_IDS or message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ Sizda ushbu bo'limga kirish huquqi yo'q.")
        return
    current_month = datetime.now().strftime("%m.%Y")
    text, kb = build_monthly_hisobot_message(month_str=current_month)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("mhisobot:"))
async def monthly_hisobot_callback(callback: CallbackQuery):
    if not config.ADMIN_IDS or callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    month_str = callback.data.split(":", 1)[1]
    text, kb = build_monthly_hisobot_message(month_str=month_str)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("hisobot_page:"))
async def hisobot_page_handler(callback: CallbackQuery):
    if not config.ADMIN_IDS or callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[1])
    text, kb = build_hisobot_message(page=page)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("paid_toggle:"))
async def paid_toggle_handler(callback: CallbackQuery):
    if not config.ADMIN_IDS or callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    parts = callback.data.split(":")
    act_id = int(parts[1])
    page = int(parts[2])
    toggle_act_paid(act_id)
    text, kb = build_hisobot_message(page=page)
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass
    await callback.answer("✅ Holat o'zgartirildi!")


@router.message(F.text.startswith("/myid"))
async def my_id_handler(message: Message):
    await message.answer(
        f"Sizning Telegram ID'ingiz: <code>{message.from_user.id}</code>\n\n"
        f"Admin huquqi olish uchun config.py faylidagi "
        f"ADMIN_IDS ro'yxatiga shu raqamni qo'shing.",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Smeta (rasxod) kiritish
# ---------------------------------------------------------------------------
@router.callback_query(F.data.startswith("smeta_open:"))
async def smeta_open_handler(callback: CallbackQuery, state: FSMContext):
    if not config.ADMIN_IDS or callback.from_user.id not in config.ADMIN_IDS:
        await callback.answer("⛔ Ruxsat yo'q!", show_alert=True)
        return
    parts = callback.data.split(":")
    act_id = int(parts[1])
    page = int(parts[2])
    await state.update_data(smeta_act_id=act_id, smeta_page=page)
    await state.set_state(AdminForm.smeta_summa)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"smeta_cancel:{page}")]
    ])
    await callback.message.edit_text(
        f"📝 <b>№{act_id:04d}</b> akti uchun rasxod summani yozing (so'mda):\n"
        f"<i>Masalan: 7700000</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("smeta_cancel:"))
async def smeta_cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    page = int(callback.data.split(":")[1])
    text, kb = build_hisobot_message(page=page)
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.message(AdminForm.smeta_summa)
async def smeta_summa_handler(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", ".")
    try:
        rasxod = int(float(text))
        if rasxod < 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Iltimos, musbat son kiriting (masalan: 7700000).")
        return

    data = await state.get_data()
    act_id = data["smeta_act_id"]
    page = data.get("smeta_page", 0)
    update_act_rasxod(act_id, rasxod)
    await state.clear()

    # Akt jamisini DB dan olamiz
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT jami FROM acts WHERE id=?", (act_id,)).fetchone()
    conn.close()
    jami_act = row[0] if row else 0
    foyda = jami_act - rasxod
    foyda_sign = "+" if foyda >= 0 else ""

    await message.answer(
        f"✅ Smeta saqlandi!\n\n"
        f"📝 Rasxod: <b>{format_money(rasxod)}</b>\n"
        f"🧾 Akt summasi: <b>{format_money(jami_act)}</b>\n"
        f"✨ Foyda: <b>{foyda_sign}{format_money(foyda)}</b>",
        parse_mode="HTML",
    )
    text, kb = build_hisobot_message(page=page)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


# ---------------------------------------------------------------------------
# Kirim kiritish (Korzinkadan kelgan pul)
# ---------------------------------------------------------------------------
@router.message(F.text == "💵 Kirim kiritish")
async def kirim_start(message: Message, state: FSMContext):
    if not config.ADMIN_IDS or message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ Sizda ushbu bo'limga kirish huquqi yo'q.")
        return
    await state.set_state(AdminForm.kirim_summa)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="kirim_cancel")]
    ])
    await message.answer(
        "💰 <b>Kirim kiritish</b>\n\n"
        "Korzinkadan kelgan summani yozing (so'mda):\n"
        "<i>Masalan: 9400000</i>",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "kirim_cancel")
async def kirim_cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Kirim bekor qilindi.")
    await callback.answer()


@router.message(AdminForm.kirim_summa)
async def kirim_summa_handler(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", ".")
    try:
        summa = int(float(text))
        if summa <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Iltimos, musbat son kiriting (masalan: 9400000).")
        return

    await state.update_data(kirim_summa_val=summa)
    await state.set_state(AdminForm.kirim_izoh)
    cancel_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Izoхsiz saqlash", callback_data="kirim_save_no_izoh")]
    ])
    await message.answer(
        f"💰 Summa: <b>{format_money(summa)}</b>\n\n"
        f"📝 Izoh yozing (masalan: <i>Oktyabr oyi, do'kon K-234</i>)\n"
        f"yoki pastdagi tugma orqali izoхsiz saqlang:",
        reply_markup=cancel_kb,
        parse_mode="HTML",
    )


@router.callback_query(AdminForm.kirim_izoh, F.data == "kirim_save_no_izoh")
async def kirim_save_no_izoh(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    summa = data["kirim_summa_val"]
    sana = datetime.now().strftime("%d.%m.%Y")
    add_kirim(summa, "", sana)
    await state.clear()
    s = get_hisobot_summary()
    await callback.message.edit_text(
        f"✅ Kirim saqlandi!\n\n"
        f"💰 Keldi: <b>{format_money(summa)}</b>\n"
        f"🔴 Qolgan qarz: <b>{format_money(s['qarz'])}</b>",
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AdminForm.kirim_izoh)
async def kirim_izoh_handler(message: Message, state: FSMContext):
    izoh = message.text.strip()
    data = await state.get_data()
    summa = data["kirim_summa_val"]
    sana = datetime.now().strftime("%d.%m.%Y")
    add_kirim(summa, izoh, sana)
    await state.clear()
    s = get_hisobot_summary()
    await message.answer(
        f"✅ Kirim saqlandi!\n\n"
        f"💰 Keldi: <b>{format_money(summa)}</b>\n"
        f"📝 Izoh: {izoh}\n"
        f"🔴 Qolgan qarz: <b>{format_money(s['qarz'])}</b>",
        parse_mode="HTML",
    )


# ---------------------------------------------------------------------------
# Erkin (Shablonlarsiz) akt yaratish
# ---------------------------------------------------------------------------
@router.message(F.text == "✍️ Erkin akt")
async def custom_order_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CustomOrderForm.client_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🏢 {config.CLIENT_NAME}", callback_data="custom_default_client")]
    ])
    await message.answer(
        "Mijoz (Buyurtmachi) nomini kiriting:\n"
        f"<i>Yoki pastdagi tugmani bosing ({config.CLIENT_NAME}):</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )


@router.callback_query(CustomOrderForm.client_name, F.data == "custom_default_client")
async def custom_client_default(callback: CallbackQuery, state: FSMContext):
    await state.update_data(client_name=config.CLIENT_NAME)
    await state.set_state(CustomOrderForm.kod)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ O'tkazib yuborish", callback_data="custom_skip_kod")]
    ])
    await callback.message.edit_text(
        "Do'kon/Buyurtma kodini yozing (agar kerak bo'lmasa, o'tkazib yuboring):",
        reply_markup=kb
    )
    await callback.answer()


@router.message(CustomOrderForm.client_name)
async def custom_client_text(message: Message, state: FSMContext):
    await state.update_data(client_name=message.text.strip())
    await state.set_state(CustomOrderForm.kod)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ O'tkazib yuborish", callback_data="custom_skip_kod")]
    ])
    await message.answer(
        "Do'kon/Buyurtma kodini yozing (agar kerak bo'lmasa, o'tkazib yuboring):",
        reply_markup=kb
    )


@router.callback_query(CustomOrderForm.kod, F.data == "custom_skip_kod")
async def custom_skip_kod(callback: CallbackQuery, state: FSMContext):
    await state.update_data(kod="")
    await state.set_state(CustomOrderForm.manzil)
    await callback.message.edit_text("Manzilni yozing (masalan: Shahrisabz):")
    await callback.answer()


@router.message(CustomOrderForm.kod)
async def custom_kod_text(message: Message, state: FSMContext):
    await state.update_data(kod=message.text.strip())
    await state.set_state(CustomOrderForm.manzil)
    await message.answer("Manzilni yozing (masalan: Shahrisabz):")


@router.message(CustomOrderForm.manzil)
async def custom_manzil_text(message: Message, state: FSMContext):
    await state.update_data(manzil=message.text.strip(), items=[])
    await state.set_state(CustomOrderForm.item_name)
    await message.answer("1-xizmat nomini kiriting (masalan: Shar (arka)):")


@router.message(CustomOrderForm.item_name)
async def custom_item_name(message: Message, state: FSMContext):
    await state.update_data(current_item_name=message.text.strip())
    await state.set_state(CustomOrderForm.item_qty)
    await message.answer("Miqdorini yozing (masalan: 15 metr, 2 dona yoki 1 xizmat):")


@router.message(CustomOrderForm.item_qty)
async def custom_item_qty(message: Message, state: FSMContext):
    await state.update_data(current_item_qty=message.text.strip())
    await state.set_state(CustomOrderForm.item_price)
    await message.answer("Ushbu xizmat jami summasini yozing (so'mda, faqat raqam, masalan: 1500000):")


@router.message(CustomOrderForm.item_price)
async def custom_item_price(message: Message, state: FSMContext):
    text = message.text.strip().replace(" ", "").replace(",", ".")
    try:
        price = int(float(text))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Iltimos, musbat raqam kiriting (masalan: 1500000).")
        return

    data = await state.get_data()
    items = data.get("items", [])
    name = data["current_item_name"]
    qty = data["current_item_qty"]
    items.append((name, qty, format_money(price), price))
    
    await state.update_data(items=items)
    await state.set_state(CustomOrderForm.menu)
    await show_custom_menu(message, state)


async def show_custom_menu(message: Message, state: FSMContext):
    data = await state.get_data()
    client = data.get("client_name", config.CLIENT_NAME)
    kod = data.get("kod", "")
    manzil = data.get("manzil", "")
    items = data.get("items", [])
    
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += f"{i}. <b>{item[0]}</b> - {item[1]} - <code>{item[2]}</code>\n"
        
    jami = sum(item[3] for item in items)
    
    text = (
        f"📝 <b>ERKIN AKT TAYYORLASH</b>\n\n"
        f"🏢 Buyurtmachi: <b>{client}</b>\n"
        f"🔑 Kod: <b>{kod if kod else 'Mavjud emas'}</b>\n"
        f"📍 Manzil: <b>{manzil}</b>\n\n"
        f"📋 <b>Xizmatlar:</b>\n{items_text}\n"
        f"💰 Jami summa: <b>{format_money(jami)}</b>\n\n"
        f"Quyidagilardan birini tanlang:"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Yana xizmat qo'shish", callback_data="custom_add_item")],
        [InlineKeyboardButton(text="✅ Tayyor — Akt yaratish", callback_data="custom_done")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="custom_cancel")]
    ])
    
    if isinstance(message, CallbackQuery):
        try:
            await message.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(CustomOrderForm.menu, F.data == "custom_add_item")
async def custom_add_item_cb(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CustomOrderForm.item_name)
    try:
        await callback.message.edit_text("Keyingi xizmat nomini kiriting (masalan: Animator):")
    except Exception:
        pass
    await callback.answer()


@router.callback_query(CustomOrderForm.menu, F.data == "custom_cancel")
async def custom_cancel_cb(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.edit_text("❌ Erkin akt bekor qilindi.")
    except Exception:
        pass
    await callback.message.answer("Yangi akt boshlash uchun pastdagi tugmalardan birini bosing.", reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


@router.callback_query(CustomOrderForm.menu, F.data == "custom_done")
async def custom_done_cb(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    if not items:
        await callback.answer("⚠️ Hech qanday xizmat kiritilmadi!", show_alert=True)
        return
        
    client = data.get("client_name", config.CLIENT_NAME)
    kod = data.get("kod", "")
    manzil = data.get("manzil", "")
    sana = datetime.now().strftime("%d.%m.%Y")
    jami = sum(item[3] for item in items)
    
    # Save to db
    akt_raqami = save_act_and_get_number(kod, manzil, sana, int(jami), client_name=client)
    
    # Create PDF
    pdf_path = create_akt_pdf(
        akt_raqami=akt_raqami,
        kod=kod,
        manzil=manzil,
        sana=sana,
        items=items,
        jami=jami,
        client_name=client
    )
    
    try:
        await callback.message.edit_text(f"✅ Erkin Akt №{akt_raqami} tayyor. Jami: {format_money(jami)}")
    except Exception:
        pass
    await callback.message.answer_document(
        FSInputFile(pdf_path), caption=f"Akt №{akt_raqami} — {client}, {manzil}"
    )
    await state.clear()
    await callback.message.answer("Yangi akt boshlash uchun pastdagi tugmalardan birini bosing.", reply_markup=get_main_kb(callback.from_user.id))
    await callback.answer()


async def main():
    if not config.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN topilmadi. .env faylida BOT_TOKEN=... ni to'ldiring.")

    init_db()
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
