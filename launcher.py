"""Bir nechta Telegram botni bitta Render Background Worker ichida ishga tushiradi.

Xotirani tejash: og'ir kutubxonalar (aiogram, pydantic, firebase, reportlab...) asosiy jarayonda
BIR MARTA yuklanadi, keyin har bir bot `fork` orqali alohida jarayon bo'lib ochiladi va shu
xotirani bo'lishib ishlatadi (4 bot ≈ 200 MB; alohida-alohida ≈ 430+ MB).

Har bir bot:
  * o'z jarayonida va o'z papkasida (bots/<nom>) ishlaydi — modullari bir-biriga aralashmaydi;
  * faqat o'z sozlamalarini ko'radi: Render'dagi `QARZ__BOT_TOKEN` botga `BOT_TOKEN` bo'lib boradi,
    boshqa botlarning tokenlari va parollari unga berilmaydi;
  * polling rejimida ishlaydi (webhook/port o'zgaruvchilari olib tashlanadi);
  * yiqilsa — avtomatik qayta ishga tushadi (5 s dan 60 s gacha kutish bilan).

`<PREFIX>__BOT_TOKEN` berilmagan bot ishga tushirilmaydi — botlarni birma-bir ko'chirish mumkin.
"""
from __future__ import annotations

import gc
import importlib
import io
import logging
import os
import runpy
import signal
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
log = logging.getLogger("launcher")


@dataclass(frozen=True)
class BotSpec:
    name: str      # papka: bots/<name>
    prefix: str    # Render'dagi sozlama prefiksi: <PREFIX>__KALIT
    entry: str     # ishga tushiriladigan fayl


BOTS = (
    BotSpec("qarz", "QARZ", "main.py"),
    BotSpec("korzinka", "KORZINKA", "main.py"),
    BotSpec("sharbot", "SHARBOT", "main.py"),
    BotSpec("taqvim", "TAQVIM", "bot.py"),
    BotSpec("oldiberdi", "OLDIBERDI", "bot.py"),   # Qarz-oldi-berdi-bot
    BotSpec("swe", "SWE", "bot.py"),               # SWE oylik test boti (python-telegram-bot)
)

# Asosiy jarayonda oldindan yuklanadigan og'ir kutubxonalar (fork'dan keyin bo'lishiladi)
PRELOAD = (
    "aiogram", "aiogram.types", "aiogram.methods", "aiogram.filters", "aiogram.fsm.context",
    "aiogram.fsm.storage.memory", "aiogram.client.default", "aiogram.webhook.aiohttp_server",
    "aiohttp", "aiohttp.web", "pydantic", "firebase_admin", "firebase_admin.db", "firebase_admin.credentials",
    "firebase_admin.firestore", "google.cloud.firestore",
    "reportlab.pdfgen.canvas", "reportlab.pdfbase.ttfonts", "reportlab.lib.pagesizes",
    "telegram", "telegram.ext", "PIL.Image", "arabic_reshaper", "bidi",
    "telethon", "psycopg2", "psycopg", "psycopg.rows", "apscheduler.schedulers.asyncio", "aiosqlite", "dotenv", "sqlite3",
)

# Hamma botga beriladigan umumiy tizim o'zgaruvchilari (maxfiy emas)
SHARED_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "SSL_CERT_FILE", "SSL_CERT_DIR", "TMPDIR", "PYTHONHASHSEED")
# Polling majburiy: bular botni webhook/port rejimiga o'tkazib yuboradi
BLOCKED_KEYS = frozenset({"WEBHOOK_URL", "RENDER_EXTERNAL_URL", "PORT", "CRON_SECRET"})

MIN_BACKOFF, MAX_BACKOFF = 5.0, 60.0
STABLE_AFTER = 120.0  # shuncha soniya ishlagan bo'lsa — kutish yana 5 s dan boshlanadi


def bot_env(spec: BotSpec, environ: dict[str, str]) -> dict[str, str]:
    """`<PREFIX>__KALIT=qiymat` -> `KALIT=qiymat`; boshqa botlarning sozlamalari o'tkazilmaydi."""
    env = {k: environ[k] for k in SHARED_KEYS if k in environ}
    pre = f"{spec.prefix}__"
    for key, value in environ.items():
        if key.startswith(pre):
            inner = key[len(pre):]
            if inner and inner not in BLOCKED_KEYS:
                env[inner] = value
    env["PYTHONUNBUFFERED"] = "1"
    env.setdefault("TZ", "Asia/Tashkent")
    return env


def preload() -> None:
    for name in PRELOAD:
        try:
            importlib.import_module(name)
        except Exception as e:  # noqa: BLE001 — bitta kutubxona yo'qligi butun tizimni to'xtatmasin
            log.warning("Oldindan yuklanmadi: %s (%s)", name, e)
    gc.collect()
    gc.freeze()  # fork'dan keyin bu obyektlar sahifalari nusxalanmasin


def _child(spec: BotSpec, env: dict[str, str], write_fd: int) -> None:
    """Fork qilingan jarayon: faqat o'z muhiti bilan botni ishga tushiradi. Hech qachon qaytmaydi."""
    code = 1
    try:
        os.setsid()
        os.dup2(write_fd, 1)
        os.dup2(write_fd, 2)
        os.close(write_fd)
        # Ota jarayon oqimlarining qulflarini meros qilib olmaslik uchun yangi obyektlar
        sys.stdout = io.TextIOWrapper(os.fdopen(1, "wb", buffering=0), write_through=True)
        sys.stderr = io.TextIOWrapper(os.fdopen(2, "wb", buffering=0), write_through=True)
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGCHLD):
            signal.signal(sig, signal.SIG_DFL)
        logging.getLogger().handlers.clear()
        os.environ.clear()
        os.environ.update(env)
        bot_dir = ROOT / "bots" / spec.name
        os.chdir(bot_dir)
        sys.path.insert(0, str(bot_dir))
        sys.argv = [spec.entry]
        runpy.run_path(spec.entry, run_name="__main__")
        code = 0
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException:  # noqa: BLE001
        import traceback
        traceback.print_exc()
    finally:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        finally:
            os._exit(code)


def _pump(name: str, read_fd: int) -> None:
    with os.fdopen(read_fd, "rb") as f:
        for raw in f:
            sys.stdout.write(f"[{name}] {raw.decode(errors='replace').rstrip()}\n")
            sys.stdout.flush()


class Supervisor:
    def __init__(self, specs, environ: dict[str, str]):
        self.specs = specs
        self.environ = environ
        self.running: dict[int, tuple[BotSpec, float]] = {}   # pid -> (bot, boshlangan vaqt)
        self.backoff: dict[str, float] = {}
        self.restart_at: dict[str, float] = {}
        self.stopping = False

    def enabled(self) -> list[BotSpec]:
        out = []
        for spec in self.specs:
            if self.environ.get(f"{spec.prefix}__BOT_TOKEN"):
                out.append(spec)
            else:
                log.warning("[%s] %s__BOT_TOKEN yo'q — bu bot ishga tushirilmaydi", spec.name, spec.prefix)
        return out

    def start(self, spec: BotSpec) -> None:
        env = bot_env(spec, self.environ)
        r, w = os.pipe()
        sys.stdout.flush()
        pid = os.fork()
        if pid == 0:
            os.close(r)
            _child(spec, env, w)
        os.close(w)
        threading.Thread(target=_pump, args=(spec.name, r), daemon=True).start()
        self.running[pid] = (spec, time.monotonic())
        log.info("[%s] ishga tushdi (pid %s)", spec.name, pid)

    def _on_term(self, *_):
        self.stopping = True

    def stop_all(self) -> None:
        for pid, (spec, _) in list(self.running.items()):
            log.info("[%s] to'xtatilmoqda", spec.name)
            try:
                os.killpg(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 10
        while self.running and time.monotonic() < deadline:
            self._reap()
            time.sleep(0.2)
        for pid in list(self.running):
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def _reap(self) -> None:
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                return
            if pid == 0:
                return
            spec, started = self.running.pop(pid, (None, 0.0))
            if spec is None or self.stopping:
                continue
            ran = time.monotonic() - started
            prev = self.backoff.get(spec.name, MIN_BACKOFF / 2)
            wait = MIN_BACKOFF if ran > STABLE_AFTER else min(prev * 2, MAX_BACKOFF)
            self.backoff[spec.name] = wait
            self.restart_at[spec.name] = time.monotonic() + wait
            log.error("[%s] to'xtadi (holat %s, %.0f s ishladi) — %.0f s dan keyin qayta ishga tushadi",
                      spec.name, os.waitstatus_to_exitcode(status), ran, wait)

    def run(self, idle_without_bots: bool = False) -> int:
        specs = self.enabled()
        signal.signal(signal.SIGTERM, self._on_term)
        signal.signal(signal.SIGINT, self._on_term)
        if not specs:
            log.error("Hech bir botning tokeni berilmagan. Render > Environment: QARZ__BOT_TOKEN va h.k.")
            if not idle_without_bots:
                return 1
            while not self.stopping:  # web service yiqilib qayta-qayta deploy bo'lmasin
                time.sleep(1)
            return 0
        preload()
        log.info("Ishga tushiriladigan botlar: %s", ", ".join(s.name for s in specs))
        by_name = {s.name: s for s in specs}
        for spec in specs:
            self.start(spec)
        while not self.stopping:
            self._reap()
            now = time.monotonic()
            for name, at in list(self.restart_at.items()):
                if now >= at:
                    del self.restart_at[name]
                    self.start(by_name[name])
            time.sleep(0.5)
        self.stop_all()
        return 0


def start_health_server(sup: "Supervisor", port: int) -> None:
    """Render Web Service port kutadi: `/` va `/health` — qaysi botlar ishlayotgani. Faqat stdlib."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class H(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            names = sorted(spec.name for spec, _ in list(sup.running.values()))
            body = ("ok: " + (", ".join(names) or "botlar yoqilmagan")).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_HEAD = do_GET

        def log_message(self, *_):
            pass

    srv = ThreadingHTTPServer(("0.0.0.0", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log.info("Health server: :%s", port)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s launcher %(levelname)s %(message)s", stream=sys.stdout)
    sup = Supervisor(BOTS, dict(os.environ))
    port = os.environ.get("PORT")
    if port:  # Render Web Service rejimi
        start_health_server(sup, int(port))
    return sup.run(idle_without_bots=bool(port))


if __name__ == "__main__":
    sys.exit(main())
