"""O'quvchi natijasi bo'yicha PDF: har bir savol, tanlangan javob, to'g'ri javob va ball.

Arabcha matn (harflar, so'zlar) PDF'da to'g'ri ulanib, o'ngdan chapga chiqishi uchun
arabic_reshaper + python-bidi bilan tayyorlanadi.
"""
from __future__ import annotations

import io
import re
import time
from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FONT_DIR = Path(__file__).with_name("fonts")
_fonts_ready = False
ARABIC = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
LATIN = re.compile(r"[A-Za-z]")
# DejaVu'da yo'q harf: vasla alif (U+0671) -> oddiy alif; harakatlar saqlanadi
MISSING = str.maketrans({"\u0671": "\u0627"})
RESHAPER = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False, "support_ligatures": True})

GREEN = colors.HexColor("#1F7A3A")
RED = colors.HexColor("#B42318")
GREY = colors.HexColor("#6B6B6B")
LINE = colors.HexColor("#D0CCC4")
HEAD_BG = colors.HexColor("#EFEBE3")


def _fonts() -> None:
    """O'zbekcha ‘ ’, ✓ ✗ va arab harflari uchun DejaVu shrifti (repo ichida)."""
    global _fonts_ready
    if not _fonts_ready:
        pdfmetrics.registerFont(TTFont("DV", str(FONT_DIR / "DejaVuSans.ttf")))
        pdfmetrics.registerFont(TTFont("DV-B", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
        pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV", boldItalic="DV-B")
        _fonts_ready = True


def ar(text: str) -> str:
    """Arabcha qismi bo'lsa: harflarni ulaydi va ko'rinish tartibini o'ngdan chapga qiladi."""
    if not ARABIC.search(text):
        return text
    # Lotin harfi yoki belgi (✓ ✗ —) bilan boshlangan qator chapdan o'ngga qoladi, arabcha qism ichida aylanadi
    first = text.lstrip()[:1]
    base = "L" if LATIN.search(text) or not ARABIC.match(first) else "R"
    return get_display(RESHAPER.reshape(text.translate(MISSING)), base_dir=base)


def _st(size: float = 9, **kw) -> ParagraphStyle:
    kw.setdefault("fontName", "DV")
    return ParagraphStyle("s", fontSize=size, leading=size * 1.35, **kw)


def _p(text: str, size: float = 9, **kw) -> Paragraph:
    return Paragraph(escape(ar(text)).replace("\n", "<br/>"), _st(size, **kw))


def safe_filename(name: str) -> str:
    keep = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name.strip())
    return (keep.strip("_") or "oquvchi")[:40]


def build_pdf(bank, a, r, kind_title: str) -> bytes:
    """bank/a/r — bot.py dagi Bank, Attempt, Result obyektlari."""
    _fonts()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title=f"{kind_title} — {a.name}", author="SWE test boti")
    story = []
    uname = f"@{a.username}" if a.username else "username yo‘q"
    when = time.strftime("%d.%m.%Y %H:%M", time.localtime(a.finished or time.time()))
    mins, secs = divmod(r.seconds, 60)

    story.append(Paragraph(f"<b>Study World Education — {escape(kind_title)}: javoblar varaqasi</b>",
                           _st(14, spaceAfter=6)))
    info = [
        ["O‘quvchi", f"{a.name} ({uname}, ID {a.user_id})"],
        ["Guruh", a.group],
        ["Sana", f"{when}  ·  sarflangan vaqt: {mins} daq {secs} s"],
        ["Natija", f"{r.score}/{r.max_score} ball  →  {r.level['name']}"],
        ["Javoblar", f"to‘g‘ri {r.correct}/{len(a.order)}  ·  bilmayman {r.dont_know}  ·  vaqt tugagan {r.timeouts}"],
    ]
    cats = "  ·  ".join(f"{bank.topics[c]}: {got}/{tot}" for c, (got, tot) in r.by_cat.items())
    info.append(["Yo‘nalishlar", cats])
    t = Table([[_p(k, 9, textColor=GREY), _p(v, 9)] for k, v in info], colWidths=[30 * mm, 152 * mm])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("LINEBELOW", (0, -1), (-1, -1), 0.5, LINE)]))
    story += [t, Spacer(1, 6 * mm)]

    head = [_p(h, 8.5, fontName="DV-B") for h in ("№", "Savol", "O‘quvchi javobi", "To‘g‘ri javob", "Ball")]
    rows = [head]
    marks = []
    for n, qi in enumerate(a.order):
        q = bank.questions[qi]
        pick = a.picks[n] if n < len(a.picks) else None
        right = q.options[q.answer]
        if pick is None:
            given = "— Vaqt tugadi" if n in a.timed_out else "— Bilmayman"
            ok, pts, color = False, 0, GREY
        else:
            ok = pick == q.answer
            given = ("✓ " if ok else "✗ ") + q.options[pick]
            pts, color = (q.points if ok else 0), (GREEN if ok else RED)
        meta = f"{bank.topics[q.cat]} · {q.points} ball"
        cell = [Paragraph(f"{escape(ar(q.q))}<br/><font color='#6B6B6B' size='7.5'>{escape(meta)}</font>", _st(8.5))]
        img = bank.image_path(q)
        if img and img.is_file():
            pic = Image(str(img))
            w = 66 * mm
            pic.drawHeight, pic.drawWidth = pic.imageHeight * w / pic.imageWidth, w
            cell.append(pic)
        rows.append([_p(str(n + 1), 8.5, alignment=TA_CENTER), cell, _p(given, 8.5, textColor=color),
                     _p(right, 8.5), _p(f"{pts}/{q.points}", 8.5, alignment=TA_CENTER)])
        marks.append(ok)
    table = Table(rows, colWidths=[9 * mm, 76 * mm, 41 * mm, 41 * mm, 15 * mm], repeatRows=1)
    style = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
             ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    for i, ok in enumerate(marks, start=1):
        if not ok:
            style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FBF3F2")))
    table.setStyle(TableStyle(style))
    story.append(table)
    doc.build(story)
    return buf.getvalue()
