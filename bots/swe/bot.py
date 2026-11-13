"""SWE (Study World Education) oylik test boti: 4 bosqich.

  1-bosqich: harflar, tashdid, tanvin, madd tabiiy, maxraj, sifatlar
  2-bosqich: tajvid qoidalari va harflar
  3-bosqich: harf sifatlari, tajvid, Qur'ondan misollar
  4-bosqich: Qur'on, tajvid, aqida, fiqh

Oqim (test faqat dars vaqtida ochiladi):
  ustoz:    /ochish Ahmadjon 40 -> guruh (starosta ismi) uchun 40 daqiqaga 4 xonali kod; kod doskaga yoziladi
            /holat -> ochiq darslar; /yopish -> hammasini yopish
  o'quvchi: /start -> ism -> kod -> bosqichni tanlaydi -> 20 savol (har biriga 60 s) -> natija
  ustoz:    har test tugashi bilan Telegram'da natija va PDF javoblar varaqasi

O'qish topshirig'i: test savollaridan keyin bitta rasmda bosqichga mos 4 ta so'z beriladi, o'quvchi ularni
o'qib bitta ovozli xabar yuboradi; audio adminlarga 1–5 baholash tugmalari bilan boradi, baho qo'yilgach
o'quvchiga xabar keladi (reading.json, words/ papkasi).

Himoya: kod faqat ochiq dars vaqtida ishlaydi; bir darsda bir o'quvchi faqat bir marta topshiradi;
5 marta noto'g'ri kod -> 10 daqiqa blok; savol xabarlarini forward/saqlash taqiqlangan (protect_content).

Botga faqat ustoz tasdiqlagan savollar ("approved": true) kiradi. Bosqich uchun tasdiqlangan savol
yetmasa, o'quvchiga u «tayyorlanmoqda» deb ko'rsatiladi.

Muhit o'zgaruvchilari:
  TELEGRAM_BOT_TOKEN   (majburiy)  @BotFather tokeni
  ADMIN_IDS            (majburiy)  natija yuboriladigan Telegram ID'lar, vergul bilan
  SUPABASE_URL, SUPABASE_KEY, DB_SECRET (ixtiyoriy) natijalarni saqlash uchun
  QUESTIONS_FILE       (ixtiyoriy) savollar fayli (standart: questions.json)
"""

from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import io

import httpx
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler, ContextTypes,
                          MessageHandler, filters)

load_dotenv()
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)  # httpx URL'da bot tokenini log qiladi
log = logging.getLogger("swebot")

HERE = Path(__file__).parent
DONT_KNOW = "Bilmayman"
LETTERS = "ABCDE"
NAME_RE = re.compile(r"^[^\d/@<>]{3,60}$")
QUESTION_TIME_S = 60
RPC_PREFIX = "swe_"
TZ = ZoneInfo("Asia/Tashkent")
CODE_RE = re.compile(r"^\d{4}$")
MAX_CODE_TRIES, CODE_LOCK_S = 5, 600
# Qolgan soniyalar ko'rsatiladigan nuqtalar: 10 soniyagacha har 10 s, keyin har 2 s (Telegram cheklovi uchun)
TICKS = (50, 40, 30, 20, 10, 8, 6, 4, 2)
DEFAULT_MINUTES = 60
LONG_OPTION = 40     # bundan uzun javob telefondagi tugmaga to'liq sig'maydi



def esc(s: str) -> str:
    """HTML uchun xavfsiz qiladi; apostrofni (o'zbekcha ') o'zgartirmaydi."""
    return html.escape(s, quote=False)


# ---------------------------------------------------------------- savollar banki
@dataclass(frozen=True)
class Question:
    id: str
    cat: str
    points: int
    q: str
    options: tuple[str, ...]
    answer: int
    image: str | None = None
    source: str = ""
    stages: tuple[str, ...] = ()       # bo'sh = mavzusi bor har bosqichda; aks holda faqat shu bosqichlarda


@dataclass(frozen=True)
class Stage:
    key: str
    title: str
    desc: str
    draw: dict[str, dict[int, int]]      # mavzu -> {ball: nechta savol}

    @property
    def test_len(self) -> int:
        return sum(sum(d.values()) for d in self.draw.values())

    @property
    def max_score(self) -> int:
        return sum(p * n for d in self.draw.values() for p, n in d.items())


@dataclass(frozen=True)
class Bank:
    topics: dict[str, str]
    stages: dict[str, Stage]
    levels: list[dict]
    questions: list[Question]          # faqat tasdiqlanganlar
    advice: dict[str, str]
    root: Path = HERE
    pending: int = 0                   # tasdiq kutayotgan savollar soni

    def pool(self, topic: str, points: int, stage: str) -> list[int]:
        return [i for i, q in enumerate(self.questions)
                if q.cat == topic and q.points == points and (not q.stages or stage in q.stages)]

    def available(self, key: str) -> bool:
        st = self.stages[key]
        return all(len(self.pool(t, p, key)) >= n for t, d in st.draw.items() for p, n in d.items())

    def level_for(self, score: int, max_score: int) -> dict:
        pct = 100 * score / max_score if max_score else 0
        return [lv for lv in self.levels if pct >= lv["min_pct"]][-1]

    def image_path(self, q: Question) -> Path | None:
        return (self.root / q.image) if q.image else None


def load_readings(path: str | Path) -> tuple[int, dict[str, list[Path]]]:
    """So'zlar banki: bosqich -> so'z rasmlari ro'yxati."""
    path = Path(path)
    if not path.is_file():
        return 0, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    per_test = int(data.get("per_test", 4))
    pools: dict[str, list[Path]] = {}
    for stage, items in data["words"].items():
        imgs = [path.parent / it for it in items]
        missing = [str(p) for p in imgs if not p.is_file()]
        if missing:
            raise ValueError(f"So'z rasmi topilmadi: {missing[0]}")
        if len(imgs) < per_test:
            raise ValueError(f"{stage}-bosqich: so'zlar {per_test} tadan kam")
        pools[stage] = imgs
    return per_test, pools


def words_card(images: list[Path]) -> bytes:
    """Tanlangan so'zlarni bitta rasmga yig'adi: har so'z alohida qatorda, raqami bilan."""
    from PIL import Image, ImageDraw, ImageFont
    W, PAD, ROW_H = 900, 30, 150
    font = ImageFont.load_default(size=44) if hasattr(ImageFont, "load_default") else None
    card = Image.new("L", (W, PAD * 2 + ROW_H * len(images)), 255)
    draw = ImageDraw.Draw(card)
    for i, p in enumerate(images):
        im = Image.open(p).convert("L").point(lambda v: 255 if v > 205 else v)   # skaner fonini oqartirish
        scale = min((W - 200) / im.width, (ROW_H - 20) / im.height)
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))))
        y = PAD + i * ROW_H
        card.paste(im, ((W - 120 - im.width) // 2 + 120, y + (ROW_H - im.height) // 2))
        draw.text((40, y + ROW_H // 2 - 26), f"{i + 1}.", fill=0, font=font)
        if i:
            draw.line((40, y, W - 40, y), fill=210, width=2)
    buf = io.BytesIO()
    card.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def load_bank(path: str | Path) -> Bank:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    topics = data["topics"]
    stages = {}
    for key, raw in data["stages"].items():
        draw = {t: {int(p): int(n) for p, n in d.items() if int(n) > 0} for t, d in raw["draw"].items()}
        if any(t not in topics for t in draw):
            raise ValueError(f"{key}-bosqich: noma'lum mavzu")
        stages[key] = Stage(key, raw["title"], raw["desc"], draw)
    qs, seen, pending = [], set(), 0
    for raw in data["questions"]:
        q = Question(raw["id"], raw["cat"], int(raw["points"]), raw["q"], tuple(raw["options"]), int(raw["answer"]),
                     raw.get("image"), raw.get("source", ""), tuple(str(x) for x in raw.get("stages", [])))
        if q.id in seen:
            raise ValueError(f"Takroriy savol id: {q.id}")
        if q.cat not in topics or q.points not in (1, 2, 3):
            raise ValueError(f"{q.id}: noma'lum mavzu yoki ball")
        if not (2 <= len(q.options) <= 4) or not (0 <= q.answer < len(q.options)):
            raise ValueError(f"{q.id}: variantlar yoki to'g'ri javob noto'g'ri")
        if len(set(q.options)) != len(q.options):
            raise ValueError(f"{q.id}: bir xil variantlar bor")
        if any(k not in stages for k in q.stages):
            raise ValueError(f"{q.id}: noma'lum bosqich")
        if q.image and not (path.parent / q.image).is_file():
            raise ValueError(f"{q.id}: rasm topilmadi: {q.image}")
        seen.add(q.id)
        if raw.get("approved", False):
            qs.append(q)
        else:
            pending += 1
    levels = sorted(data["levels"], key=lambda lv: lv["min_pct"])
    if not levels or levels[0]["min_pct"] != 0:
        raise ValueError("Darajalar 0% dan boshlanishi kerak")
    return Bank(topics, stages, levels, qs, data.get("advice", {}), path.parent, pending)


# ---------------------------------------------------------------- o'quvchi sessiyasi
@dataclass
class Attempt:
    stage: str = ""
    session_id: int = 0
    closes_at: float = 0.0
    group: str = ""
    name: str = ""
    user_id: int = 0
    username: str | None = None
    step: str = "name"      # name -> code -> choose -> ready -> test -> grading -> done
    order: list[int] = field(default_factory=list)
    shuffles: list[list[int]] = field(default_factory=list)
    picks: list[int | None] = field(default_factory=list)
    timed_out: set[int] = field(default_factory=set)
    started: float = 0.0
    finished: float = 0.0
    timer: asyncio.Task | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    result_id: int | None = None
    read_words: list[Path] = field(default_factory=list)   # o'qish uchun berilgan so'zlar
    read_card: bytes = b""   # savol xabarini tahrirlash navbati


def new_test(bank: Bank, stage: str, rng: random.Random) -> tuple[list[int], list[list[int]]]:
    """Bosqichning har mavzusidan draw bo'yicha tasodifiy savollar; tartib oson -> qiyin; variantlar aralash."""
    picked: dict[int, list[int]] = {}
    for topic, draw in bank.stages[stage].draw.items():
        for pts, n in draw.items():
            picked.setdefault(pts, []).extend(rng.sample(bank.pool(topic, pts, stage), n))
    order: list[int] = []
    for pts in sorted(picked):
        chunk = picked[pts]
        rng.shuffle(chunk)
        order += chunk
    shuffles = []
    for i in order:
        idx = list(range(len(bank.questions[i].options)))
        rng.shuffle(idx)
        shuffles.append(idx)
    return order, shuffles


@dataclass
class Result:
    score: int
    max_score: int
    level: dict
    by_cat: dict[str, tuple[int, int]]
    correct: int
    dont_know: int
    timeouts: int
    seconds: int


def grade(bank: Bank, a: Attempt) -> Result:
    by_cat = {c: [0, 0] for c in bank.stages[a.stage].draw}
    score = correct = dont_know = 0
    for n, qi in enumerate(a.order):
        q = bank.questions[qi]
        by_cat[q.cat][1] += q.points
        pick = a.picks[n] if n < len(a.picks) else None
        if pick is None:
            if n not in a.timed_out:
                dont_know += 1
        elif pick == q.answer:
            score += q.points
            correct += 1
            by_cat[q.cat][0] += q.points
    end = a.finished or time.time()
    total = sum(t for _, t in by_cat.values())
    return Result(score, total, bank.level_for(score, total),
                  {c: (v[0], v[1]) for c, v in by_cat.items()}, correct, dont_know, len(a.timed_out),
                  int(end - a.started) if a.started else 0)


# ---------------------------------------------------------------- ma'lumotlar bazasi (Supabase RPC)
class Store:
    def __init__(self, url: str | None, key: str | None, secret: str | None):
        self.enabled = bool(url and key and secret)
        self.url, self.key, self.secret = (url or "").rstrip("/"), key, secret

    async def _rpc(self, fn: str, payload: dict):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{self.url}/rest/v1/rpc/{RPC_PREFIX}{fn}", json={"p_secret": self.secret, **payload},
                             headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"})
            r.raise_for_status()
            return r.json()

    async def save(self, row: dict) -> int | None:
        """Natijani saqlaydi; natija id'sini qaytaradi (saqlanmasa None)."""
        if not self.enabled:
            return None
        try:
            rid = await self._rpc("save_result", {"r": row})
            return int(rid) if rid is not None else None
        except Exception as e:  # noqa: BLE001
            log.warning("Bazaga saqlanmadi: %r", e)
            return None

    async def add_reading(self, row: dict):
        return await self._try("add_reading", {"r": row}, "Audio bazaga yozilmadi")

    async def grade_reading(self, reading_id: int, grade: int, admin: int):
        return await self._try("grade_reading", {"p_id": reading_id, "p_grade": grade, "p_admin": admin},
                               "Baho saqlanmadi")

    async def _try(self, fn: str, payload: dict, what: str):
        """RPC; xatoda (None, True) qaytaradi."""
        if not self.enabled:
            return None, True
        try:
            return await self._rpc(fn, payload), False
        except Exception as e:  # noqa: BLE001
            log.warning("%s: %r", what, e)
            return None, True

    async def open_session(self, group: str, minutes: int, admin: int):
        return await self._try("open_session", {"p_group": group, "p_minutes": minutes, "p_admin": admin}, "Dars ochilmadi")

    async def find_session(self, code: str):
        return await self._try("find_session", {"p_code": code}, "Kod tekshirilmadi")

    async def active_sessions(self):
        return await self._try("active_sessions", {}, "Ochiq darslar o'qilmadi")

    async def close_sessions(self):
        return await self._try("close_sessions", {}, "Darslar yopilmadi")

    async def has_attempt(self, tg_id: int, session_id: int):
        return await self._try("has_attempt", {"p_tg_id": tg_id, "p_session": session_id}, "Urinish tekshirilmadi")

    async def ping(self) -> None:
        if self.enabled:
            try:
                await self._rpc("ping", {})
                log.info("Baza bilan aloqa bor")
            except Exception as e:  # noqa: BLE001
                log.warning("Baza javob bermadi (Supabase loyihasi uxlab qolgan bo'lishi mumkin): %r", e)


# ---------------------------------------------------------------- matnlar
def ts(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def hhmm(t: float) -> str:
    return datetime.fromtimestamp(t, TZ).strftime("%H:%M")


def bar(got: int, total: int, width: int = 10) -> str:
    filled = round(width * got / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def progress(n: int, total: int, width: int = 10) -> str:
    filled = round(width * n / total) if total else 0
    return "▓" * filled + "░" * (width - filled) + f"  {n}/{total}"


def question_head(bank: Bank, a: Attempt, n: int) -> str:
    q = bank.questions[a.order[n]]
    return (f"{progress(n + 1, len(a.order))}  ·  {esc(bank.topics[q.cat])}\n\n"
            f"<b>{n + 1}. {esc(q.q)}</b>")


def options_text(bank: Bank, a: Attempt, n: int) -> str:
    q = bank.questions[a.order[n]]
    return "\n".join(f"<b>{LETTERS[pos]})</b> {esc(q.options[orig])}" for pos, orig in enumerate(a.shuffles[n]))


def timer_line(left: int) -> str:
    """Qolgan vaqt satri. Oxirgi 10 soniyada «yonish»: olov ko'payib boradi."""
    if left > 10:
        filled = round(10 * left / QUESTION_TIME_S)
        return f"⏳ <b>{left}</b> soniya  " + "▓" * filled + "░" * (10 - filled)
    fire = "🔥" * min(5, (12 - left) // 2)
    return f"{fire} <b>{left} SONIYA QOLDI!</b> {fire}"


def question_view(bank: Bank, a: Attempt, n: int, left: int | None = None) -> tuple[str, InlineKeyboardMarkup]:
    """Har javob — alohida tugma, o'quvchi javobning o'zini bosadi.
    Telefonda tugmaga sig'maydigan uzun javobli savollarda variantlar to'liq matni xabarda ham beriladi."""
    q = bank.questions[a.order[n]]
    rows = [[InlineKeyboardButton(f"{LETTERS[pos]}) {q.options[orig]}", callback_data=f"a:{n}:{pos}")]
            for pos, orig in enumerate(a.shuffles[n])]
    rows.append([InlineKeyboardButton(f"🤷 {DONT_KNOW}", callback_data=f"a:{n}:x")])
    left = QUESTION_TIME_S if left is None else left
    body = question_head(bank, a, n)
    if any(len(o) > LONG_OPTION for o in q.options):
        body += "\n\n" + options_text(bank, a, n)
    return f"{body}\n\n{timer_line(int(left))}", InlineKeyboardMarkup(rows)


def answered_text(bank: Bank, a: Attempt, n: int, pos: int | None, timeout: bool = False) -> str:
    q = bank.questions[a.order[n]]
    if timeout:
        tail = "⏰ <i>Vaqt tugadi</i>"
    elif pos is None:
        tail = f"✔️ <i>Javobingiz: 🤷 {DONT_KNOW}</i>"
    else:
        tail = f"✔️ <i>Javobingiz: {LETTERS[pos]}) {esc(q.options[a.shuffles[n][pos]])}</i>"
    return f"{question_head(bank, a, n)}\n\n{tail}"


def stage_view(bank: Bank) -> tuple[str, InlineKeyboardMarkup]:
    rows, lines = [], []
    for key, st in bank.stages.items():
        ok = bank.available(key)
        lines.append(f"<b>{esc(st.title)}</b> — {esc(st.desc)}" + ("" if ok else " <i>(tayyorlanmoqda)</i>"))
        rows.append([InlineKeyboardButton(("" if ok else "⏳ ") + st.title, callback_data=f"s:{key}")])
    text = "📚 <b>Qaysi bosqich testini topshirasiz?</b>\n\n" + "\n".join(lines)
    return text, InlineKeyboardMarkup(rows)


def cat_lines(bank: Bank, by_cat: dict, prev: dict | None = None) -> list[str]:
    out = []
    for c, (got, tot) in by_cat.items():
        pct = round(100 * got / tot) if tot else 0
        line = f"{bar(got, tot)} {pct:>3}%  {esc(bank.topics[c])}"
        if prev and c in prev:
            pgot, ptot = prev[c]
            ppct = round(100 * pgot / ptot) if ptot else 0
            line += f"  ({ppct}% → {pct}%)"
        out.append(line)
    return out


def weak_cats(by_cat: dict) -> list[str]:
    return [c for c, (got, tot) in by_cat.items() if tot and got / tot < 0.5]


def stage_title(bank: Bank, a: Attempt) -> str:
    st = bank.stages.get(a.stage)
    return f"{st.title} testi" if st else "Test"


def student_report(bank: Bank, a: Attempt, r: Result) -> str:
    lines = [f"✅ <b>{esc(stage_title(bank, a))} yakunlandi!</b>", "",
             f"Natija: <b>{r.score}/{r.max_score}</b> ball  ·  daraja: <b>{esc(r.level['name'])}</b>",
             "", "Yo'nalishlar bo'yicha:"] + cat_lines(bank, r.by_cat)
    weak = weak_cats(r.by_cat)
    if weak:
        lines += ["", "📚 <b>Sizga tavsiya:</b>"]
        lines += [f"• <b>{esc(bank.topics[c])}:</b> {esc(bank.advice[c])}" for c in weak if c in bank.advice]
    lines += ["", "Natijangiz ustozga yuborildi."]
    return "\n".join(lines)


def admin_report(bank: Bank, a: Attempt, r: Result, saved: bool) -> str:
    uname = f"@{a.username}" if a.username else "username yo'q"
    mins, secs = divmod(r.seconds, 60)
    lines = [f"📋 <b>{esc(stage_title(bank, a))}: yangi natija</b>", "",
             f"👤 {esc(a.name)} ({esc(uname)}, ID <code>{a.user_id}</code>)",
             f"👥 Guruh: <b>{esc(a.group)}</b>",
             f"🎯 Ball: <b>{r.score}/{r.max_score}</b> → <b>{esc(r.level['name'])}</b>",
             f"✔️ To'g'ri: {r.correct}/{len(a.order)}  ·  🤷 Bilmayman: {r.dont_know}  ·  "
             f"⏰ Vaqt tugagan: {r.timeouts}  ·  ⏱ {mins} daq {secs} s",
             "", "<b>Yo'nalishlar:</b>"] + cat_lines(bank, r.by_cat)
    weak = weak_cats(r.by_cat)
    if weak:
        lines += ["", "⚠️ Bo'sh joylar: " + esc(", ".join(bank.topics[c] for c in weak))]
    lines += ["", f"💡 {esc(r.level.get('note', ''))}"]
    if r.seconds and r.seconds < 150:
        lines.append("❗ Test juda tez topshirilgan (2,5 daqiqadan kam): javoblar tasodifiy bo'lishi mumkin.")
    if not saved:
        lines.append("⚠️ Natija bazaga saqlanmadi (faqat shu xabarda bor).")
    return "\n".join(lines)


# ---------------------------------------------------------------- handlerlar
@dataclass
class BotState:
    bank: Bank
    admins: set[int]
    store: Store
    rng: random.Random = field(default_factory=random.Random)
    photo_ids: dict[str, str] = field(default_factory=dict)   # rasm yo'li -> Telegram file_id (qayta yuklamaslik uchun)
    read_per_test: int = 0
    read_pools: dict[str, list[Path]] = field(default_factory=dict)


def state(ctx: ContextTypes.DEFAULT_TYPE) -> BotState:
    return ctx.application.bot_data["state"]


def attempt(ctx: ContextTypes.DEFAULT_TYPE) -> Attempt:
    if "attempt" not in ctx.user_data:
        ctx.user_data["attempt"] = Attempt()
    return ctx.user_data["attempt"]


def cancel_timer(a: Attempt) -> None:
    if a.timer and not a.timer.done():
        a.timer.cancel()
    a.timer = None


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    old = ctx.user_data.get("attempt")
    if old and old.step in ("test", "grading", "reading"):
        # testni /start bilan qayta boshlab, savollarni ko'paytirib bo'lmaydi
        await update.effective_message.reply_text("Test davom etyapti. Avval uni yakunlang.")
        return
    if old:
        cancel_timer(old)
    user = update.effective_user
    ctx.user_data["attempt"] = Attempt(user_id=user.id, username=user.username)
    intro = ("Assalomu alaykum! 👋\n\nBu — Study World Education o'quv markazining <b>oylik testi</b>.\n\n"
             "• Test faqat dars vaqtida, ustoz bergan <b>4 xonali kod</b> bilan ochiladi\n"
             "• 4 bosqich bor, siz o'z bosqichingizni tanlaysiz\n"
             f"• 20 ta savol, har biriga {QUESTION_TIME_S} soniya\n"
             "• Javobni bilmasangiz, «Bilmayman»ni bosing — taxmin qilmang\n"
             "• Testni kitob yoki boshqa yordamisiz, o'zingiz bajaring\n\n")
    await update.effective_message.reply_text(intro + "Ism-familiyangizni yozing:", parse_mode="HTML")


async def _admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    if user.id in state(ctx).admins:
        return True
    log.info("Admin bo'lmagan foydalanuvchi buyruq yubordi: id=%s username=%s text=%r",
             user.id, user.username, (update.effective_message.text or "")[:40])
    await update.effective_message.reply_text(
        f"Bu buyruq faqat ustoz (admin) uchun.\nSizning Telegram ID: {user.id}\n"
        "Admin bo'lishingiz kerak bo'lsa, shu raqamni bot egasiga yuboring.")
    return False


async def cmd_id(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    role = "admin" if user.id in state(ctx).admins else "o'quvchi"
    await update.effective_message.reply_text(f"Sizning Telegram ID: {user.id} ({role})")


async def cmd_ochish(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _admin(update, ctx):
        return
    st, msg = state(ctx), update.effective_message
    args = list(ctx.args or [])
    minutes = DEFAULT_MINUTES
    if args and args[-1].isdigit():
        minutes = int(args.pop())
    group = " ".join(args).strip()[:40]
    if not group or not (5 <= minutes <= 240):
        await msg.reply_text("Foydalanish: /ochish Ahmadjon 40\n(guruh nomi yoki starosta ismi, keyin necha daqiqa "
                             f"ochiq turishi: 5–240; daqiqa yozilmasa {DEFAULT_MINUTES})")
        return
    res, err = await st.store.open_session(group, minutes, update.effective_user.id)
    if err or not res:
        await msg.reply_text("⚠️ Darsni ochib bo'lmadi: baza javob bermadi. Birozdan keyin qayta urinib ko'ring.")
        return
    await msg.reply_text(
        f"✅ <b>Test ochildi</b>\n👥 Guruh: <b>{esc(res['group_name'])}</b>\n"
        f"⏰ {hhmm(ts(res['closes_at']))} gacha ({minutes} daqiqa)\n\n"
        f"🔑 Kod: <code>{res['code']}</code>\n\n"
        f"Kodni doskaga yozing. O'quvchilar botni ochib (@{ctx.bot.username}) /start bosadi va shu kodni kiritadi.\n"
        "Darsdan keyin /yopish bilan yopishingiz mumkin, aks holda vaqt tugaganda o'zi yopiladi.",
        parse_mode="HTML")


async def cmd_holat(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _admin(update, ctx):
        return
    res, err = await state(ctx).store.active_sessions()
    if err:
        await update.effective_message.reply_text("⚠️ Baza javob bermadi.")
        return
    if not res:
        await update.effective_message.reply_text("Hozir ochiq dars yo'q. Ochish: /ochish Ahmadjon 40")
        return
    lines = ["<b>Ochiq darslar:</b>"] + [
        f"• {esc(s['group_name'])}: kod <code>{s['code']}</code>, {hhmm(ts(s['closes_at']))} gacha, "
        f"topshirganlar: {s['done']}" for s in res]
    await update.effective_message.reply_text("\n".join(lines), parse_mode="HTML")


async def cmd_yopish(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _admin(update, ctx):
        return
    n, err = await state(ctx).store.close_sessions()
    await update.effective_message.reply_text("⚠️ Baza javob bermadi." if err else f"🔒 Yopildi: {n or 0} ta dars. "
                                              "Test boshlagan o'quvchilar uni oxirigacha yakunlay oladi.")


async def check_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, text: str) -> None:
    msg = update.effective_message
    now = time.time()
    locked = ctx.user_data.get("code_lock", 0)
    if locked > now:
        await msg.reply_text(f"⛔ Ko'p marta noto'g'ri kod kiritildi. {int((locked - now) // 60) + 1} daqiqadan keyin "
                             "urinib ko'ring.")
        return
    if not CODE_RE.match(text):
        await msg.reply_text("Kod 4 ta raqamdan iborat. Ustoz doskaga yozgan kodni kiriting:")
        return
    st = state(ctx)
    res, err = await st.store.find_session(text)
    if err:
        await msg.reply_text("⚠️ Kodni hozir tekshirib bo'lmadi. Bir daqiqadan keyin qayta yozing.")
        return
    if not res:
        tries = ctx.user_data.get("code_tries", 0) + 1
        ctx.user_data["code_tries"] = tries
        if tries >= MAX_CODE_TRIES:
            ctx.user_data["code_lock"], ctx.user_data["code_tries"] = now + CODE_LOCK_S, 0
            await msg.reply_text("⛔ Kod 5 marta noto'g'ri kiritildi. 10 daqiqadan keyin urinib ko'ring.")
        else:
            await msg.reply_text("❌ Kod noto'g'ri yoki test hozir yopiq. Test faqat dars vaqtida ochiladi.")
        return
    ctx.user_data["code_tries"] = 0
    done, err = await st.store.has_attempt(a.user_id, int(res["id"]))
    if err:
        await msg.reply_text("⚠️ Hozir tekshirib bo'lmadi. Bir daqiqadan keyin kodni qayta yozing.")
        return
    if done:
        a.step = "done"
        await msg.reply_text("Siz bu darsdagi testni topshirib bo'lgansiz. Har darsda bir marta topshiriladi.")
        return
    a.session_id, a.group, a.closes_at = int(res["id"]), res["group_name"], ts(res["closes_at"])
    await ask_stage(ctx, msg, a)


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    a = attempt(ctx)
    msg = update.effective_message
    text = (msg.text or "").strip()
    if a.step == "name":
        if not NAME_RE.match(text):
            await msg.reply_text("Ism-familiyangizni to'liq yozing (masalan: Aliyev Vali).")
            return
        a.name = " ".join(text.split())
        if not a.user_id:
            a.user_id, a.username = update.effective_user.id, update.effective_user.username
        a.step = "code"
        await msg.reply_text("🔑 Ustoz doskaga yozgan 4 xonali kodni kiriting:")
    elif a.step == "code":
        await check_code(update, ctx, a, text)
    elif a.step == "test":
        await msg.reply_text("Javobni savol ostidagi tugmalar orqali tanlang.")
    elif a.step == "reading":
        await msg.reply_text("So'zlarni yozmang — ovoz chiqarib o'qing va ovozli xabar yuboring (🎤 tugmasini bosib turing).")
    elif a.step == "grading":
        await msg.reply_text("⏳ Natija tayyorlanmoqda, biroz kuting.")
    elif a.step in ("choose", "ready"):
        await msg.reply_text("Yuqoridagi tugmalardan birini tanlang.")
    else:
        await msg.reply_text("Yangi test faqat keyingi darsda, ustoz bergan kod bilan ochiladi. Boshlash: /start")


async def ask_stage(ctx: ContextTypes.DEFAULT_TYPE, msg, a: Attempt) -> None:
    a.step = "choose"
    t, kb = stage_view(state(ctx).bank)
    await msg.reply_text(t, parse_mode="HTML", reply_markup=kb)


async def on_stage(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    a = attempt(ctx)
    st = state(ctx)
    key = query.data.split(":", 1)[1]
    if a.step == "name" and not a.name:
        await query.answer()
        await lost_test(query)
        return
    if a.step != "choose" or key not in st.bank.stages:
        await query.answer()
        return
    if not st.bank.available(key):
        await query.answer("Bu bosqich savollari hali tayyorlanmoqda. Boshqa bosqichni tanlang.", show_alert=True)
        return
    await query.answer()
    a.stage, a.step = key, "ready"
    stage = st.bank.stages[key]
    await query.edit_message_text(f"📚 <b>{esc(stage.title)}</b> — {esc(stage.desc)}", parse_mode="HTML")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("▶️ Testni boshlash", callback_data="begin")],
                               [InlineKeyboardButton("↩️ Boshqa bosqich", callback_data="back")]])
    extra = ("\nQur'on savollarida mushafdan olingan rasm chiqadi: qizil ramkadagi so'zga qarang.\n"
             if "quron" in stage.draw else "")
    await query.message.reply_text(
        f"{esc(a.name)}, guruh: <b>{esc(a.group)}</b>\n\n"
        f"{stage.test_len} ta savol, har biriga {QUESTION_TIME_S} soniya.\n{extra}\nTayyor bo'lsangiz, bosing:",
        parse_mode="HTML", reply_markup=kb)


async def on_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    a = attempt(ctx)
    if a.step != "ready":
        return
    a.stage = ""
    await query.edit_message_reply_markup(None)
    await ask_stage(ctx, query.message, a)


async def send_question(ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, chat_id: int, n: int) -> None:
    st = state(ctx)
    text, kb = question_view(st.bank, a, n)
    q = st.bank.questions[a.order[n]]
    img = st.bank.image_path(q)
    if img:
        key = str(img)
        photo = st.photo_ids.get(key)
        if photo is None:
            with img.open("rb") as f:
                sent = await ctx.bot.send_photo(chat_id, InputFile(f, filename=img.name), caption=text,
                                                parse_mode="HTML", reply_markup=kb, protect_content=True)
            if getattr(sent, "photo", None):
                st.photo_ids[key] = sent.photo[-1].file_id
        else:
            sent = await ctx.bot.send_photo(chat_id, photo, caption=text, parse_mode="HTML", reply_markup=kb,
                                            protect_content=True)
    else:
        sent = await ctx.bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=kb, protect_content=True)
    cancel_timer(a)
    a.timer = asyncio.create_task(question_timeout(ctx, a, chat_id, sent.message_id, n, bool(img)))


async def edit_answered(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, msg_id: int, text: str, is_photo: bool) -> None:
    try:
        if is_photo:
            await ctx.bot.edit_message_caption(chat_id=chat_id, message_id=msg_id, caption=text, parse_mode="HTML")
        else:
            await ctx.bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, parse_mode="HTML")
    except Exception as e:  # noqa: BLE001 — xabar o'chirilgan bo'lishi mumkin
        log.debug("edit: %r", e)


async def edit_question(ctx: ContextTypes.DEFAULT_TYPE, chat_id: int, msg_id: int, text: str,
                        kb: InlineKeyboardMarkup, is_photo: bool) -> None:
    """Taymerni yangilash; xato bo'lsa (cheklov, xabar o'chirilgan) jim o'tkazib yuboriladi."""
    try:
        if is_photo:
            await ctx.bot.edit_message_caption(chat_id=chat_id, message_id=msg_id, caption=text, parse_mode="HTML",
                                               reply_markup=kb)
        else:
            await ctx.bot.edit_message_text(text, chat_id=chat_id, message_id=msg_id, parse_mode="HTML",
                                            reply_markup=kb)
    except asyncio.CancelledError:
        raise
    except Exception as e:  # noqa: BLE001
        log.debug("timer edit: %r", e)


async def question_timeout(ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, chat_id: int, msg_id: int, n: int,
                           is_photo: bool) -> None:
    st = state(ctx)
    try:
        start = time.monotonic()
        for left in TICKS:
            if left >= QUESTION_TIME_S:
                continue
            await asyncio.sleep(max(0.0, start + QUESTION_TIME_S - left - time.monotonic()))
            async with a.lock:
                if a.step != "test" or len(a.picks) != n:
                    return
                text, kb = question_view(st.bank, a, n, left)
                await edit_question(ctx, chat_id, msg_id, text, kb, is_photo)
        await asyncio.sleep(max(0.0, start + QUESTION_TIME_S - time.monotonic()))
    except asyncio.CancelledError:
        return
    if a.step != "test" or len(a.picks) != n:
        return
    a.picks.append(None)      # await'dan oldin: javob bilan poyga bo'lmasin
    a.timed_out.add(n)
    a.timer = None
    async with a.lock:
        await edit_answered(ctx, chat_id, msg_id, answered_text(st.bank, a, n, None, timeout=True), is_photo)
    await advance(ctx, a, chat_id)


async def advance(ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, chat_id: int) -> None:
    if len(a.picks) < len(a.order):
        await send_question(ctx, a, chat_id, len(a.picks))
        return
    a.finished = time.time()
    await finish_in_chat(ctx, a, chat_id)


async def lost_test(query) -> None:
    try:
        await query.edit_message_reply_markup(None)
    except Exception:  # noqa: BLE001
        pass
    await query.message.reply_text(
        "⚠️ Server qayta ishga tushgani uchun test uzilib qoldi, natija saqlanmadi.\n\n"
        "/start bosing va ustoz bergan kodni qayta kiriting: test boshidan, yangi savollar bilan boshlanadi.")


async def on_begin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    a = attempt(ctx)
    if a.step == "name" and not a.name:
        await lost_test(query)
        return
    if a.step != "ready":
        return
    if a.closes_at and time.time() > a.closes_at:
        a.step = "done"
        await query.edit_message_text("🔒 Test vaqti tugadi. Keyingi darsda ustoz yangi kod beradi.")
        return
    st = state(ctx)
    a.order, a.shuffles = new_test(st.bank, a.stage, st.rng)
    a.picks, a.timed_out = [], set()
    a.started = time.time()
    a.step = "test"
    await query.edit_message_text("▶️ Test boshlandi. Omad!")
    await send_question(ctx, a, query.message.chat_id, 0)


async def on_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    a = attempt(ctx)
    st = state(ctx)
    try:
        _, n_str, choice = query.data.split(":")
        n = int(n_str)
    except ValueError:
        await query.answer()
        return
    if a.step == "name" and not a.order:
        # server qayta ishga tushgan: xotiradagi test yo'qolgan
        await query.answer("Test uzilib qoldi. /start bosib qaytadan kiring.", show_alert=True)
        await lost_test(query)
        return
    if a.step != "test" or n != len(a.picks):
        await query.answer("Bu savolga javob berilgan yoki vaqti tugagan.")
        return
    pos = None if choice == "x" else int(choice)
    if pos is not None and not (0 <= pos < len(a.shuffles[n])):
        await query.answer()
        return
    a.picks.append(None if pos is None else a.shuffles[n][pos])   # await'dan oldin
    cancel_timer(a)
    await query.answer("✅ Qabul qilindi")
    is_photo = bool(getattr(query.message, "photo", None))
    async with a.lock:
        await edit_answered(ctx, query.message.chat_id, query.message.message_id,
                            answered_text(st.bank, a, n, pos), is_photo)
    await advance(ctx, a, query.message.chat_id)


async def finish_in_chat(ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, chat_id: int) -> None:
    if a.step in ("grading", "done"):
        return
    a.step = "grading"
    st = state(ctx)
    wait = await ctx.bot.send_message(chat_id, "⏳ Natija tayyorlanmoqda…")
    r = grade(st.bank, a)
    user_id = a.user_id or chat_id
    row = {"kind": "oylik", "stage": int(a.stage), "session_id": a.session_id or None, "tg_id": user_id, "username": a.username, "full_name": a.name,
           "group_name": a.group, "score": r.score, "max_score": r.max_score, "level": r.level["name"],
           "by_cat": {c: list(v) for c, v in r.by_cat.items()}, "correct": r.correct, "dont_know": r.dont_know,
           "timeouts": r.timeouts, "seconds": r.seconds}
    a.result_id = await st.store.save(row)
    saved = a.result_id is not None
    a.step = "done"
    try:
        await wait.delete()
    except Exception:  # noqa: BLE001
        pass
    await ctx.bot.send_message(chat_id, student_report(st.bank, a, r), parse_mode="HTML", protect_content=True)
    report = admin_report(st.bank, a, r, saved or not st.store.enabled)
    log.info("%s-bosqich yakunlandi: %s, %s, %d/%d", a.stage, a.group, a.name, r.score, r.max_score)
    pdf = None
    try:
        from pdfreport import build_pdf, safe_filename
        data = await asyncio.to_thread(build_pdf, st.bank, a, r, stage_title(st.bank, a))
        pdf = (data, f"{a.stage}-bosqich_{safe_filename(a.group)}_{safe_filename(a.name)}.pdf")
    except Exception:  # noqa: BLE001 — PDF bo'lmasa ham matnli hisobot ketadi
        log.exception("PDF yasab bo'lmadi")
    for admin in st.admins:
        try:
            await ctx.bot.send_message(admin, report, parse_mode="HTML")
            if pdf:
                await ctx.bot.send_document(admin, document=pdf[0], filename=pdf[1],
                                            caption=f"📄 Javoblar varaqasi: {a.name}"[:1000])
        except Exception as e:  # noqa: BLE001 — admin botga /start bosmagan bo'lishi mumkin
            log.warning("Adminga yuborilmadi %s: %r", admin, e)
    await start_reading(ctx, a, chat_id)


# ---------------------------------------------------------------- o'qish (audio) topshirig'i
MIN_VOICE_S, MAX_VOICE_S = 3, 300


async def start_reading(ctx: ContextTypes.DEFAULT_TYPE, a: Attempt, chat_id: int) -> None:
    st = state(ctx)
    pool = st.read_pools.get(a.stage, [])
    if not st.read_per_test or len(pool) < st.read_per_test:
        await ctx.bot.send_message(chat_id, "Test yakunlandi. Rahmat!")
        return
    a.read_words = st.rng.sample(pool, st.read_per_test)
    a.read_card = await asyncio.to_thread(words_card, a.read_words)
    a.step = "reading"
    await ctx.bot.send_photo(
        chat_id, InputFile(io.BytesIO(a.read_card), filename="sozlar.png"), protect_content=True, parse_mode="HTML",
        caption=(f"🎤 <b>O'qish topshirig'i</b>\n\nRasmdagi {len(a.read_words)} ta so'zni tartib bilan, tajvid "
                 "qoidalariga rioya qilib o'qing va <b>bitta ovozli xabar</b> yuboring "
                 "(🎤 tugmasini bosib turib gapiring). Ovozli xabarni ustoz eshitib baholaydi."))


def grade_kb(reading_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"{g} ⭐", callback_data=f"rg:{reading_id}:{g}")
                                  for g in range(1, 6)]])


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    a = attempt(ctx)
    msg = update.effective_message
    if a.step != "reading":
        await msg.reply_text("Hozir ovozli xabar kutilmayapti. O'qish topshirig'ini bajarayotgan bo'lsangiz va "
                             "bot shunday javob bersa, ustozga ayting (server qayta ishga tushgan bo'lishi mumkin).")
        return
    media = msg.voice or msg.audio
    duration = int(getattr(media, "duration", 0) or 0)
    if duration < MIN_VOICE_S:
        await msg.reply_text("Ovozli xabar juda qisqa. 4 ta so'zning hammasini o'qib, qayta yuboring.")
        return
    if duration > MAX_VOICE_S:
        await msg.reply_text("Ovozli xabar juda uzun. Faqat rasmdagi 4 ta so'zni o'qib, qayta yuboring.")
        return
    st = state(ctx)
    a.step = "done"                                      # await'dan oldin: ikkinchi audio qabul qilinmaydi
    text_id = ",".join(p.stem for p in a.read_words)
    rid, err = await st.store.add_reading({
        "result_id": a.result_id, "tg_id": a.user_id or msg.chat_id, "full_name": a.name, "group_name": a.group,
        "stage": int(a.stage), "idx": 1, "total": 1, "text_id": text_id[:40], "file_id": media.file_id,
        "duration": duration})
    head = (f"🎤 <b>O'qish: {esc(a.name)}</b>\n👥 {esc(a.group)}  ·  {esc(stage_title(st.bank, a))}\n"
            f"⏱ {duration} s")
    for admin in st.admins:
        try:
            await ctx.bot.send_photo(admin, InputFile(io.BytesIO(a.read_card), filename="sozlar.png"),
                                     caption=head + "\n📖 O'qilishi kerak bo'lgan so'zlar", parse_mode="HTML")
            kb = grade_kb(rid) if rid else None
            tail = "\n\nBaho qo'ying:" if rid else "\n\n⚠️ Baza ishlamadi: bu audioga baho saqlanmaydi."
            if msg.voice:
                await ctx.bot.send_voice(admin, media.file_id, caption=head + tail, parse_mode="HTML", reply_markup=kb)
            else:
                await ctx.bot.send_audio(admin, media.file_id, caption=head + tail, parse_mode="HTML", reply_markup=kb)
        except Exception as e:  # noqa: BLE001
            log.warning("Audio adminga yuborilmadi %s: %r", admin, e)
    if err:
        log.warning("Audio bazaga yozilmadi: %s", a.name)
    await msg.reply_text("✅ Rahmat! O'qishingiz ustozga yuborildi. Ustoz baholagach, bahoni shu yerga yuboraman.")


async def on_grade(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    st = state(ctx)
    if update.effective_user.id not in st.admins:
        await query.answer("Baholash faqat ustoz uchun.", show_alert=True)
        return
    try:
        _, rid, g = query.data.split(":")
        rid, g = int(rid), int(g)
    except ValueError:
        await query.answer()
        return
    if not 1 <= g <= 5:
        await query.answer()
        return
    res, err = await st.store.grade_reading(rid, g, update.effective_user.id)
    if err or not res:
        await query.answer("Baho saqlanmadi, qayta bosing.", show_alert=True)
        return
    await query.answer(f"✅ {g}/5 saqlandi")
    caption = (query.message.caption_html or "").split("\n\nBaho")[0]
    try:
        await query.edit_message_caption(caption=f"{caption}\n\n✅ Baho: <b>{g}/5</b> (o'zgartirish mumkin)",
                                         parse_mode="HTML", reply_markup=grade_kb(rid))
    except Exception as e:  # noqa: BLE001 — bir xil baho qayta bosilsa
        log.debug("grade edit: %r", e)
    if res.get("notify"):
        try:
            await ctx.bot.send_message(res["tg_id"], f"🎤 <b>Ustoz o'qishingizni baholadi: {g}/5</b>",
                                       parse_mode="HTML")
        except Exception as e:  # noqa: BLE001
            log.warning("O'quvchiga baho yuborilmadi: %r", e)
        await query.message.reply_text(f"📊 {esc(res['full_name'])}: o'qish bahosi {g}/5. O'quvchiga yuborildi.",
                                       parse_mode="HTML")


async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Handler xatosi", exc_info=ctx.error)


def parse_ids(raw: str | None) -> set[int]:
    return {int(x) for x in (raw or "").replace(" ", "").split(",") if x.lstrip("-").isdigit()}


def build_app(token: str, st: BotState) -> Application:
    async def post_init(app: Application) -> None:
        await st.store.ping()

    app = Application.builder().token(token).post_init(post_init).build()
    app.bot_data["state"] = st
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ochish", cmd_ochish))
    app.add_handler(CommandHandler("holat", cmd_holat))
    app.add_handler(CommandHandler("yopish", cmd_yopish))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CallbackQueryHandler(on_stage, pattern=r"^s:\w+$"))
    app.add_handler(CallbackQueryHandler(on_back, pattern=r"^back$"))
    app.add_handler(CallbackQueryHandler(on_begin, pattern=r"^begin$"))
    app.add_handler(CallbackQueryHandler(on_answer, pattern=r"^a:"))
    app.add_handler(CallbackQueryHandler(on_grade, pattern=r"^rg:\d+:\d$"))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    return app


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")   # bots-hub'da: SWE__BOT_TOKEN
    admins = parse_ids(os.getenv("ADMIN_IDS"))
    if not token or not admins:
        raise SystemExit("TELEGRAM_BOT_TOKEN va ADMIN_IDS majburiy (.env yoki server sozlamalari)")
    bank = load_bank(os.getenv("QUESTIONS_FILE", HERE / "questions.json"))
    st = BotState(bank, admins, Store(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"), os.getenv("DB_SECRET")))
    st.read_per_test, st.read_pools = load_readings(HERE / "reading.json")
    log.info("O'qish so'zlari: %s (har testda %d ta)",
             ", ".join(f"{k}-bosqich {len(v)}" for k, v in sorted(st.read_pools.items())), st.read_per_test)
    log.info("Adminlar ID: %s", ", ".join(map(str, sorted(admins))))
    log.info("Bank: %d tasdiqlangan savol, %d ta tasdiq kutmoqda; ochiq bosqichlar: %s; adminlar: %d; baza: %s",
             len(bank.questions), bank.pending, ",".join(k for k in bank.stages if bank.available(k)) or "yo'q",
             len(admins), "bor" if st.store.enabled else "yo'q")
    app = build_app(token, st)
    base_url = os.getenv("WEBHOOK_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if base_url:
        app.run_webhook(listen="0.0.0.0", port=int(os.getenv("PORT", "10000")), url_path="webhook",
                        webhook_url=f"{base_url.rstrip('/')}/webhook",
                        secret_token=os.getenv("WEBHOOK_SECRET") or None,
                        allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    else:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
