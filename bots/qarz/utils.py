"""Umumiy yordamchi funksiyalar: validatsiya va formatlash."""
from __future__ import annotations

import re

_AMOUNT_RE = re.compile(r"^\d+([.,]\d{1,2})?$")


def validate_amount(text: str) -> float | None:
    """Foydalanuvchi kiritgan summani tekshiradi.

    Faqat musbat sonlarga (butun yoki 2 xonagacha kasr) ruxsat beriladi.
    Noto'g'ri bo'lsa None qaytaradi.
    """
    if not text:
        return None
    text = text.strip().replace(" ", "").replace(",", ".")
    if not _AMOUNT_RE.match(text):
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    if value <= 0:
        return None
    # Doniya/tiyin darajasidagi xatoliklarni oldini olish uchun 2 xonaga yaxlitlaymiz
    return round(value, 2)


def format_amount(value: float, currency: str) -> str:
    """1500000 -> '1,500,000 UZS' ko'rinishida formatlaydi."""
    if float(value).is_integer():
        formatted = f"{int(value):,}"
    else:
        formatted = f"{value:,.2f}"
    return f"{formatted} {currency}"


def format_datetime(dt) -> str:
    """Sana va vaqtni '22.08.2026 11:24' ko'rinishida formatlaydi."""
    if dt is None:
        return "—"
    # datetime obyekti bo'lsa
    try:
        return dt.strftime("%d.%m.%Y %H:%M")
    except AttributeError:
        pass
    # SQLite dan kelgan ISO string bo'lsa: '2026-08-22T06:24:45.968196+00:00'
    try:
        from datetime import datetime, timezone, timedelta
        s = str(dt).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        # UTC+5 ga o'tkazamiz
        d = d.astimezone(timezone(timedelta(hours=5)))
        return d.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(dt)
