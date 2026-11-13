import asyncio
import json
import random
import time
from datetime import datetime, timezone
from collections import Counter
from unittest.mock import AsyncMock, MagicMock

import pytest

import bot

BANK = bot.load_bank(bot.HERE / "questions.json")


@pytest.fixture(scope="module")
def full_bank(tmp_path_factory):
    """Hamma savollar tasdiqlangandek: 1–3-bosqichlarni ham sinash uchun."""
    data = json.loads((bot.HERE / "questions.json").read_text(encoding="utf-8"))
    for q in data["questions"]:
        q["approved"] = True
    p = tmp_path_factory.mktemp("b") / "questions.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (p.parent / "images").symlink_to(bot.HERE / "images")
    return bot.load_bank(p)


def test_only_approved_questions_used():
    raw = json.loads((bot.HERE / "questions.json").read_text(encoding="utf-8"))["questions"]
    approved = {q["id"] for q in raw if q.get("approved")}
    assert {q.id for q in BANK.questions} == approved and BANK.pending == len(raw) - len(approved)
    assert "qr23" not in {q["id"] for q in raw}
    assert all(q.source for q in BANK.questions)


def test_stage_availability_now():
    assert all(BANK.available(k) for k in BANK.stages) and BANK.pending == 0
    ids = {q.id for q in BANK.questions}
    assert not ids & {"h12", "s03", "s04", "s06", "s09", "s07", "s11"}       # ustoz o'chirgan
    by_id = {q.id: q for q in BANK.questions}
    assert by_id["m06"].options[by_id["m06"].answer].startswith("2 harakat")


def test_all_stages_twenty_questions(full_bank):
    assert all(full_bank.available(k) for k in full_bank.stages)
    for key, st in full_bank.stages.items():
        assert st.test_len == 20
        for seed in range(25):
            order, sh = bot.new_test(full_bank, key, random.Random(seed))
            qs = [full_bank.questions[i] for i in order]
            assert len(set(order)) == 20 and {q.cat for q in qs} == set(st.draw)
            assert [q.points for q in qs] == sorted(q.points for q in qs)          # oson -> qiyin
            per = Counter((q.cat, q.points) for q in qs)
            assert all(per[(t, p)] == n for t, d in st.draw.items() for p, n in d.items())
            assert sum(q.points for q in qs) == st.max_score


def test_stage_topics_match_request(full_bank):
    s = full_bank.stages
    assert set(s["1"].draw) == {"harf", "madd", "maxraj", "sifat"}
    assert "tajvid" in s["2"].draw and "harf" in s["2"].draw
    assert set(s["3"].draw) == {"sifat", "tajvid", "quron"}
    assert set(s["4"].draw) == {"quron", "aqida", "fiqh", "tajvid"}


def test_teacher_fixes_kept():
    by_id = {q.id: q for q in BANK.questions}
    assert by_id["t12"].options[by_id["t12"].answer] == "4 alifdan 6 alifgacha (vojib)"
    assert by_id["t13"].options[by_id["t13"].answer] == "2, 4 yoki 5 alif"
    for i in ("qr04", "qr09"):
        assert by_id[i].options[by_id[i].answer] == "Izhor shafaviy (mim izhori)"


def test_levels_by_percent():
    assert BANK.level_for(14, 36)["name"] == "Boshlang'ich"          # 39%
    assert BANK.level_for(16, 40)["name"] == "O'rta"                 # 40%
    assert BANK.level_for(29, 40)["name"] == "O'rta"
    assert BANK.level_for(27, 36)["name"] == "Yuqori"                # 75%


def test_grade_timeouts_and_dontknow():
    a = bot.Attempt(stage="4", started=0)
    a.order, a.shuffles = bot.new_test(BANK, "4", random.Random(1))
    a.picks = [BANK.questions[i].answer for i in a.order[:10]] + [None] * 10
    a.timed_out = {15, 16, 17}
    r = bot.grade(BANK, a)
    assert r.correct == 10 and r.timeouts == 3 and r.dont_know == 7 and r.max_score == 40
    assert set(r.by_cat) == {"quron", "tajvid", "aqida", "fiqh"}


def test_question_view_answers_on_buttons():
    long_seen = short_seen = False
    for seed in range(15):
        a = bot.Attempt(stage="4")
        a.order, a.shuffles = bot.new_test(BANK, "4", random.Random(seed))
        for n in range(20):
            text, kb = bot.question_view(BANK, a, n)
            q = BANK.questions[a.order[n]]
            labels = [b.text for row in kb.inline_keyboard for b in row]
            assert all(len(row) == 1 for row in kb.inline_keyboard)            # har javob o'z qatorida
            assert labels == [f"{bot.LETTERS[p]}) {q.options[o]}" for p, o in enumerate(a.shuffles[n])] + \
                [f"🤷 {bot.DONT_KNOW}"]
            listed = "<b>A)</b>" in text
            if any(len(o) > bot.LONG_OPTION for o in q.options):
                assert listed
                long_seen = True
            else:
                assert not listed
                short_seen = True
            if q.image:
                assert len(text) <= 1024
    assert long_seen and short_seen


def test_stage_view_all_open():
    text, kb = bot.stage_view(BANK)
    labels = [b.text for row in kb.inline_keyboard for b in row]
    assert labels == ["1-bosqich", "2-bosqich", "3-bosqich", "4-bosqich"] and "tayyorlanmoqda" not in text


def test_reports_no_entrance_wording():
    a = bot.Attempt(stage="4", group="<g>", name="Ali & Vali", user_id=5, started=0)
    a.order, a.shuffles = bot.new_test(BANK, "4", random.Random(2))
    a.picks = [None] * 20
    r = bot.grade(BANK, a)
    rep = bot.admin_report(BANK, a, r, saved=True)
    st = bot.student_report(BANK, a, r)
    assert "&lt;g&gt;" in rep and "Ali &amp; Vali" in rep and "4-bosqich testi" in rep
    assert "saqlanmadi" in bot.admin_report(BANK, a, r, saved=False)
    assert "Sizga tavsiya" in st
    for t in (rep, st):
        assert "kirish" not in t.lower() and "yakuniy" not in t.lower()


class FakeStore:
    enabled = True

    def __init__(self):
        self.rows, self.sessions, self.down = [], {}, False

    async def save(self, row):
        self.rows.append(row)
        return len(self.rows)

    async def add_reading(self, row):
        self.readings = getattr(self, "readings", [])
        self.readings.append(dict(row, grade=None))
        return len(self.readings), False

    async def grade_reading(self, rid, grade, admin):
        rd = self.readings[rid - 1]
        rd["grade"] = grade
        same = [r for r in self.readings if r["result_id"] == rd["result_id"]]
        graded = [r["grade"] for r in same if r["grade"] is not None]
        notify = len(graded) >= rd["total"] and not getattr(self, "notified", False)
        if notify:
            self.notified = True
        return {"tg_id": rd["tg_id"], "full_name": rd["full_name"], "grades": [r["grade"] for r in same],
                "graded": len(graded), "total": rd["total"], "notify": notify}, False

    async def ping(self):
        pass

    async def open_session(self, group, minutes, admin):
        sid = len(self.sessions) + 1
        code = f"{1000 + sid}"
        closes = datetime.fromtimestamp(time.time() + minutes * 60, timezone.utc).isoformat()
        self.sessions[code] = {"id": sid, "code": code, "group_name": group, "closes_at": closes, "done": 0}
        return self.sessions[code], False

    async def find_session(self, code):
        if self.down:
            return None, True
        s = self.sessions.get(code)
        return (s if s and bot.ts(s["closes_at"]) > time.time() else None), False

    async def active_sessions(self):
        return [s for s in self.sessions.values() if bot.ts(s["closes_at"]) > time.time()], False

    async def close_sessions(self):
        n = len(self.sessions)
        for s in self.sessions.values():
            s["closes_at"] = datetime.fromtimestamp(time.time() - 1, timezone.utc).isoformat()
        return n, False

    async def has_attempt(self, tg_id, session_id):
        return any(r["tg_id"] == tg_id and r["session_id"] == session_id for r in self.rows), False


def _ctx(bank=BANK, store=None):
    ctx = MagicMock()
    ctx.user_data = {}
    ctx.application.bot_data = {"state": bot.BotState(bank, {111}, store or FakeStore(), random.Random(3))}
    sent = MagicMock(message_id=42)
    sent.delete = AsyncMock()
    photo = MagicMock(message_id=43)
    photo.photo = [MagicMock(file_id="small"), MagicMock(file_id="FILEID")]
    ctx.bot.send_message = AsyncMock(return_value=sent)
    ctx.bot.send_photo = AsyncMock(return_value=photo)
    ctx.bot.send_document = AsyncMock()
    ctx.bot.edit_message_text = AsyncMock()
    ctx.bot.edit_message_caption = AsyncMock()
    ctx.bot.username = "testbot"
    return ctx


def _upd(uid=7):
    msg = MagicMock()
    msg.reply_text = AsyncMock()
    msg.chat_id = uid
    upd = MagicMock()
    upd.effective_message = msg
    upd.effective_user = MagicMock(id=uid, username="ali")
    q = MagicMock()
    q.answer = AsyncMock()
    q.edit_message_text = AsyncMock()
    q.edit_message_reply_markup = AsyncMock()
    q.message.reply_text = AsyncMock()
    q.message.chat_id = uid
    q.message.message_id = 42
    q.message.photo = []
    upd.callback_query = q
    return upd, msg, q


def _open(ctx, group="15-guruh", minutes=60):
    st = ctx.application.bot_data["state"]
    res, _ = asyncio.run(st.store.open_session(group, minutes, 111))
    return res["code"]


def _start(ctx, upd, msg, code=None):
    code = code or _open(ctx)
    ctx.args = []
    asyncio.run(bot.cmd_start(upd, ctx))
    hello = msg.reply_text.await_args.args[0]
    assert "oylik testi" in hello and "kirish" not in hello.lower() and "kod" in hello
    msg.text = "Aliyev Vali"
    asyncio.run(bot.on_text(upd, ctx))
    a = ctx.user_data["attempt"]
    assert a.step == "code"
    msg.text = code
    asyncio.run(bot.on_text(upd, ctx))
    return a


def _play(ctx, upd, q, a, choose):
    async def play():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        for n in range(20):
            q.data = choose(n, a)
            await bot.on_answer(upd, ctx)
        assert a.timer is None
    asyncio.run(play())


def test_unavailable_stage_refused(tmp_path):
    data = json.loads((bot.HERE / "questions.json").read_text(encoding="utf-8"))
    for q in data["questions"]:
        if q["cat"] == "harf":
            q["approved"] = False
    p = tmp_path / "questions.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "images").symlink_to(bot.HERE / "images")
    ctx = _ctx(bot.load_bank(p))
    upd, msg, q = _upd()
    a = _start(ctx, upd, msg)
    assert a.step == "choose"
    q.data = "s:1"
    asyncio.run(bot.on_stage(upd, ctx))
    assert a.step == "choose" and "tayyorlanmoqda" in q.answer.await_args.args[0]
    q.data = "s:9"
    asyncio.run(bot.on_stage(upd, ctx))
    assert a.step == "choose"


def test_full_flow_stage4_with_photos_and_pdf():
    store = FakeStore()
    ctx = _ctx(store=store)
    upd, msg, q = _upd()
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))
    assert a.stage == "4" and a.step == "ready"
    right = lambda n, a: f"a:{n}:{a.shuffles[n].index(BANK.questions[a.order[n]].answer)}"
    _play(ctx, upd, q, a, lambda n, a: right(n, a) if n % 2 == 0 else f"a:{n}:x")
    assert a.step == "done"
    row = store.rows[0]
    assert row["kind"] == "oylik" and row["stage"] == 4 and row["group_name"] == "15-guruh" and row["tg_id"] == 7
    assert row["session_id"] == a.session_id
    n_photo = sum(1 for qi in a.order if BANK.questions[qi].image)
    assert n_photo == 5 and ctx.bot.send_photo.await_count == 5
    admin_msgs = [c for c in ctx.bot.send_message.await_args_list if c.args[0] == 111]
    assert len(admin_msgs) == 1 and "4-bosqich testi" in admin_msgs[0].args[1]
    doc = ctx.bot.send_document.await_args
    assert doc.args[0] == 111 and doc.kwargs["document"][:5] == b"%PDF-" and "4-bosqich" in doc.kwargs["filename"]


def test_stage1_flow_when_approved_and_back_button(full_bank):
    store = FakeStore()
    ctx = _ctx(full_bank, store)
    upd, msg, q = _upd(8)
    a = _start(ctx, upd, msg, code=_open(ctx, "Kechki guruh"))
    q.data = "s:2"
    asyncio.run(bot.on_stage(upd, ctx))
    q.data = "back"
    asyncio.run(bot.on_back(upd, ctx))
    assert a.step == "choose" and a.stage == ""
    q.data = "s:1"
    asyncio.run(bot.on_stage(upd, ctx))
    _play(ctx, upd, q, a, lambda n, a: f"a:{n}:{a.shuffles[n].index(full_bank.questions[a.order[n]].answer)}")
    row = store.rows[0]
    assert row["stage"] == 1 and row["score"] == row["max_score"] == full_bank.stages["1"].max_score and row["group_name"] == "Kechki guruh"
    assert set(row["by_cat"]) == {"harf", "madd", "maxraj", "sifat"}
    assert ctx.bot.send_photo.await_count == 0


def test_bad_callback_ignored():
    ctx = _ctx()
    upd, msg, q = _upd()
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))

    async def play():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        q.data = "a:0:9"
        await bot.on_answer(upd, ctx)
        q.data = "a:5:0"
        await bot.on_answer(upd, ctx)
        assert a.picks == []
        bot.cancel_timer(a)
    asyncio.run(play())


def test_question_timeout(monkeypatch):
    monkeypatch.setattr(bot, "QUESTION_TIME_S", 0.05)
    ctx = _ctx()
    upd, msg, q = _upd(9)
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))

    async def play():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        await asyncio.sleep(0.2)
        assert a.picks[:1] == [None] and 0 in a.timed_out
        q.data = "a:0:0"
        await bot.on_answer(upd, ctx)
        assert q.answer.await_args.args[0].startswith("Bu savolga")
        bot.cancel_timer(a)
    asyncio.run(play())
    edited = [c.args[0] for c in ctx.bot.edit_message_text.await_args_list] + \
             [c.kwargs.get("caption", "") for c in ctx.bot.edit_message_caption.await_args_list]
    assert any("Vaqt tugadi" in t for t in edited)


def test_admin_commands_only_for_admin():
    ctx = _ctx()
    upd, msg, _ = _upd(999)
    for cmd in (bot.cmd_ochish, bot.cmd_holat, bot.cmd_yopish):
        ctx.args = ["Ahmadjon", "40"]
        asyncio.run(cmd(upd, ctx))
        out = msg.reply_text.await_args.args[0]
        assert "faqat ustoz" in out and "999" in out
    assert ctx.application.bot_data["state"].store.sessions == {}
    asyncio.run(bot.cmd_id(upd, ctx))
    assert "999" in msg.reply_text.await_args.args[0] and "o'quvchi" in msg.reply_text.await_args.args[0]


def test_open_status_close_flow():
    ctx = _ctx()
    upd, msg, _ = _upd(111)
    ctx.args = ["Ahmadjon", "aka", "45"]
    asyncio.run(bot.cmd_ochish(upd, ctx))
    out = msg.reply_text.await_args.args[0]
    store = ctx.application.bot_data["state"].store
    code = next(iter(store.sessions))
    assert f"<code>{code}</code>" in out and "Ahmadjon aka" in out and "45 daqiqa" in out
    ctx.args = []
    asyncio.run(bot.cmd_holat(upd, ctx))
    assert code in msg.reply_text.await_args.args[0]
    asyncio.run(bot.cmd_yopish(upd, ctx))
    assert "Yopildi: 1" in msg.reply_text.await_args.args[0]
    asyncio.run(bot.cmd_holat(upd, ctx))
    assert "ochiq dars yo'q" in msg.reply_text.await_args.args[0]
    ctx.args = ["15-guruh", "999"]
    asyncio.run(bot.cmd_ochish(upd, ctx))
    assert "Foydalanish" in msg.reply_text.await_args.args[0]


def test_wrong_code_and_lock():
    ctx = _ctx()
    _open(ctx)
    upd, msg, _ = _upd()
    ctx.args = []
    asyncio.run(bot.cmd_start(upd, ctx))
    msg.text = "Aliyev Vali"
    asyncio.run(bot.on_text(upd, ctx))
    a = ctx.user_data["attempt"]
    msg.text = "12"
    asyncio.run(bot.on_text(upd, ctx))
    assert "4 ta raqam" in msg.reply_text.await_args.args[0]
    for _ in range(5):
        msg.text = "9999"
        asyncio.run(bot.on_text(upd, ctx))
    assert "5 marta" in msg.reply_text.await_args.args[0]
    msg.text = "1001"                                   # to'g'ri kod ham blok vaqtida qabul qilinmaydi
    asyncio.run(bot.on_text(upd, ctx))
    assert "Ko'p marta" in msg.reply_text.await_args.args[0] and a.step == "code"


def test_closed_session_and_db_down():
    ctx = _ctx()
    code = _open(ctx)
    store = ctx.application.bot_data["state"].store
    asyncio.run(store.close_sessions())
    upd, msg, _ = _upd()
    ctx.args = []
    asyncio.run(bot.cmd_start(upd, ctx))
    msg.text = "Aliyev Vali"
    asyncio.run(bot.on_text(upd, ctx))
    msg.text = code
    asyncio.run(bot.on_text(upd, ctx))
    assert "yopiq" in msg.reply_text.await_args.args[0]
    store.down = True
    asyncio.run(bot.on_text(upd, ctx))
    assert "tekshirib bo'lmadi" in msg.reply_text.await_args.args[0]


def test_one_attempt_per_lesson_and_restart_blocked():
    store = FakeStore()
    ctx = _ctx(store=store)
    upd, msg, q = _upd()
    code = _open(ctx)
    a = _start(ctx, upd, msg, code)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))

    async def first_answer():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        q.data = "a:0:x"
        await bot.on_answer(upd, ctx)
    asyncio.run(first_answer())
    asyncio.run(bot.cmd_start(upd, ctx))                 # test o'rtasida /start
    assert "davom etyapti" in msg.reply_text.await_args.args[0] and ctx.user_data["attempt"] is a

    async def rest():
        for n in range(1, 20):
            q.data = f"a:{n}:x"
            await bot.on_answer(upd, ctx)
    asyncio.run(rest())
    assert a.step == "done" and store.rows[0]["session_id"] == a.session_id
    a2 = _start(ctx, upd, msg, code)                     # shu darsda ikkinchi marta
    assert a2.step == "done" and "topshirib bo'lgansiz" in msg.reply_text.await_args.args[0]


def test_session_expired_before_begin():
    ctx = _ctx()
    upd, msg, q = _upd()
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))
    a.closes_at = time.time() - 1
    q.data = "begin"
    asyncio.run(bot.on_begin(upd, ctx))
    assert a.step == "done" and "vaqti tugadi" in q.edit_message_text.await_args.args[0]


def test_questions_are_protected():
    ctx = _ctx()
    upd, msg, q = _upd()
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))

    async def play():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        bot.cancel_timer(a)
    asyncio.run(play())
    calls = ctx.bot.send_message.await_args_list + ctx.bot.send_photo.await_args_list
    sent_q = [c for c in calls if c.kwargs.get("reply_markup") is not None]
    assert sent_q and all(c.kwargs.get("protect_content") for c in sent_q)


def test_store_uses_swe_functions():
    s = bot.Store("https://x.supabase.co", "k", "sec")
    calls = []

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return "ok"

    class Client:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def post(self, url, json, headers):
            calls.append((url, json))
            return Resp()
    import httpx
    orig = httpx.AsyncClient
    httpx.AsyncClient = Client
    try:
        asyncio.run(s.ping())
        asyncio.run(s.save({"a": 1}))
    finally:
        httpx.AsyncClient = orig
    assert calls[0][0].endswith("/rest/v1/rpc/swe_ping")
    assert calls[1][0].endswith("/rest/v1/rpc/swe_save_result") and calls[1][1]["r"] == {"a": 1}


def test_build_app():
    app = bot.build_app("123:ABC", bot.BotState(BANK, {1}, FakeStore()))
    assert len(app.handlers[0]) == 12


def test_pdf_report(full_bank):
    from pdfreport import build_pdf
    for key in ("1", "4"):
        a = bot.Attempt(stage=key, group="Sinov", name="Ali Valiyev", user_id=1)
        a.order, a.shuffles = bot.new_test(full_bank, key, random.Random(1))
        a.picks = [full_bank.questions[qi].answer if n % 2 else None for n, qi in enumerate(a.order)]
        a.started, a.finished = 1000.0, 1300.0
        data = build_pdf(full_bank, a, bot.grade(full_bank, a), f"{key}-bosqich testi")
        assert data[:5] == b"%PDF-" and len(data) > 5000


def test_lost_attempt_after_restart_explained():
    ctx = _ctx()
    upd, msg, q = _upd()
    for data, handler in (("a:17:0", bot.on_answer), ("begin", bot.on_begin), ("s:4", bot.on_stage)):
        ctx.user_data.clear()                      # server qayta ishga tushgandek
        q.message.reply_text.reset_mock()
        q.data = data
        asyncio.run(handler(upd, ctx))
        assert "uzilib qoldi" in q.message.reply_text.await_args.args[0]


def test_stage2_only_questions_not_in_stage1(full_bank):
    only2 = {"m10", "h11", "m13"}
    assert {q.id: q.stages for q in BANK.questions if q.id in only2} == {i: ("2",) for i in only2}
    seen = {"1": set(), "2": set()}
    for key in seen:
        for seed in range(300):
            order, _ = bot.new_test(BANK, key, random.Random(seed))
            seen[key].update(BANK.questions[i].id for i in order)
    assert not seen["1"] & only2 and only2 <= seen["2"]


def test_timer_line():
    assert "60" in bot.timer_line(60) and "▓" * 10 in bot.timer_line(60)
    assert "🔥" not in bot.timer_line(20)
    assert bot.timer_line(10).count("🔥") == 2 and bot.timer_line(2).count("🔥") == 10
    assert "SONIYA QOLDI" in bot.timer_line(4)


def test_countdown_edits_keep_buttons_and_stop_after_answer(monkeypatch):
    monkeypatch.setattr(bot, "QUESTION_TIME_S", 0.4)
    monkeypatch.setattr(bot, "TICKS", (0.3, 0.2, 0.1))
    ctx = _ctx()
    upd, msg, q = _upd(9)
    a = _start(ctx, upd, msg)
    q.data = "s:4"
    asyncio.run(bot.on_stage(upd, ctx))

    async def play():
        q.data = "begin"
        await bot.on_begin(upd, ctx)
        await asyncio.sleep(0.6)                     # 1-savol: taymer yangilanib, vaqt tugaydi
        edits = ctx.bot.edit_message_text.await_args_list
        ticks = [c for c in edits if c.kwargs.get("reply_markup") is not None and "1/20" in c.args[0]]
        assert len(ticks) == 3 and all("SONIYA QOLDI" in c.args[0] for c in ticks)
        assert "Vaqt tugadi" in edits[3].args[0] and "1/20" in edits[3].args[0]
        n_before = len(edits)
        q.data = "a:1:x"                               # 2-savolga darhol javob
        await bot.on_answer(upd, ctx)
        await asyncio.sleep(0.15)
        new = ctx.bot.edit_message_text.await_args_list[n_before:]
        answered = [i for i, c in enumerate(new) if "2/20" in c.args[0] and c.kwargs.get("reply_markup") is None]
        assert answered and "Bilmayman" in new[answered[0]].args[0]
        # javobdan keyin 2-savol taymeri savolni (tugmalar bilan) qayta yozmaydi
        assert not any("2/20" in c.args[0] and c.kwargs.get("reply_markup") is not None for c in new[answered[0]:])
        bot.cancel_timer(a)
    asyncio.run(play())


def _reading_ctx():
    store = FakeStore()
    ctx = _ctx(store=store)
    st = ctx.application.bot_data["state"]
    st.read_per_test, st.read_pools = bot.load_readings(bot.HERE / "reading.json")
    ctx.bot.send_voice = AsyncMock()
    ctx.bot.send_audio = AsyncMock()
    return ctx, store


def test_reading_pools_valid():
    per, pools = bot.load_readings(bot.HERE / "reading.json")
    assert per == 4 and set(pools) == {"1", "2", "3", "4"}
    assert all(len(p) >= 40 for p in pools.values())
    card = bot.words_card(pools["1"][:4])
    assert card[:8] == b"\x89PNG\r\n\x1a\n"


def _finish_test(ctx, upd, msg, q, stage="4"):
    a = _start(ctx, upd, msg)
    q.data = f"s:{stage}"
    asyncio.run(bot.on_stage(upd, ctx))
    _play(ctx, upd, q, a, lambda n, a: f"a:{n}:x")
    return a


def _voice(msg, seconds, fid="VOICE"):
    msg.voice = MagicMock(duration=seconds, file_id=fid)
    msg.audio = None


def test_reading_flow_and_grading():
    ctx, store = _reading_ctx()
    upd, msg, q = _upd()
    a = _finish_test(ctx, upd, msg, q, stage="1")
    assert a.step == "reading" and len(a.read_words) == 4 and len(set(a.read_words)) == 4 and a.result_id == 1
    card_msgs = [c for c in ctx.bot.send_photo.await_args_list if c.args[0] == 7 and "O'qish" in c.kwargs["caption"]]
    assert len(card_msgs) == 1 and card_msgs[0].kwargs["protect_content"]
    msg.text = "matn"
    asyncio.run(bot.on_text(upd, ctx))
    assert "ovozli xabar" in msg.reply_text.await_args.args[0]
    _voice(msg, 1)
    asyncio.run(bot.on_voice(upd, ctx))
    assert "juda qisqa" in msg.reply_text.await_args.args[0] and a.step == "reading"
    asyncio.run(bot.cmd_start(upd, ctx))
    assert "davom etyapti" in msg.reply_text.await_args.args[0]
    _voice(msg, 12, "V1")
    asyncio.run(bot.on_voice(upd, ctx))
    assert a.step == "done" and len(store.readings) == 1 and store.readings[0]["total"] == 1
    _voice(msg, 12, "V2")                                  # ikkinchi audio qabul qilinmaydi
    asyncio.run(bot.on_voice(upd, ctx))
    assert len(store.readings) == 1 and ctx.bot.send_voice.await_count == 1
    kb = ctx.bot.send_voice.await_args.kwargs["reply_markup"]
    assert [b.callback_data for b in kb.inline_keyboard[0]] == [f"rg:1:{g}" for g in range(1, 6)]

    qa = MagicMock()
    qa.answer, qa.edit_message_caption = AsyncMock(), AsyncMock()
    qa.message.caption_html = "🎤 <b>O'qish</b>\n\nBaho qo'ying:"
    qa.message.reply_text = AsyncMock()
    gu = MagicMock(callback_query=qa, effective_user=MagicMock(id=7))
    qa.data = "rg:1:5"
    asyncio.run(bot.on_grade(gu, ctx))
    assert store.readings[0]["grade"] is None
    gu.effective_user = MagicMock(id=111)
    qa.data = "rg:1:4"
    asyncio.run(bot.on_grade(gu, ctx))
    to_student = [c for c in ctx.bot.send_message.await_args_list if c.args[0] == 7 and "baholadi" in c.args[1]]
    assert len(to_student) == 1 and "4/5" in to_student[0].args[1]
    assert "Baho: <b>4/5</b>" in qa.edit_message_caption.await_args.kwargs["caption"]


def test_voice_when_not_expected():
    ctx, _ = _reading_ctx()
    upd, msg, _ = _upd()
    _voice(msg, 10)
    asyncio.run(bot.on_voice(upd, ctx))
    assert "kutilmayapti" in msg.reply_text.await_args.args[0]
