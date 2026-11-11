import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import launcher  # noqa: E402


def test_env_isolated_and_polling_forced():
    environ = {"PATH": "/usr/bin", "QARZ__BOT_TOKEN": "1:a", "QARZ__ADMIN_IDS": "5", "QARZ__WEBHOOK_URL": "https://x",
               "SHARBOT__BOT_TOKEN": "2:b", "SHARBOT__DATABASE_URL": "postgres://secret", "RENDER_EXTERNAL_URL": "https://h"}
    env = launcher.bot_env(launcher.BotSpec("qarz", "QARZ", "main.py"), environ)
    assert env["BOT_TOKEN"] == "1:a" and env["ADMIN_IDS"] == "5" and env["PATH"] == "/usr/bin"
    assert "WEBHOOK_URL" not in env and "RENDER_EXTERNAL_URL" not in env       # polling majburiy
    assert "DATABASE_URL" not in env and not any(k.startswith("SHARBOT") for k in env)  # boshqa bot siri yo'q


def test_supervisor_runs_restarts_and_stops(tmp_path):
    for name, body in {"good": "import os,time\nprint('TOKEN', os.environ['BOT_TOKEN'], flush=True)\ntime.sleep(60)\n",
                       "bad": "raise SystemExit(3)\n"}.items():
        d = tmp_path / "bots" / name
        d.mkdir(parents=True)
        (d / "main.py").write_text(body)
    script = textwrap.dedent(f"""
        import sys, logging
        sys.path.insert(0, {str(Path(launcher.__file__).parent)!r})
        import launcher
        from pathlib import Path
        launcher.ROOT = Path({str(tmp_path)!r})
        launcher.PRELOAD = ()
        launcher.MIN_BACKOFF = 0.5
        bots = (launcher.BotSpec("good", "GOOD", "main.py"), launcher.BotSpec("bad", "BAD", "main.py"),
                launcher.BotSpec("off", "OFF", "main.py"))
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        sys.exit(launcher.Supervisor(bots, {{"PATH": "/usr/bin", "GOOD__BOT_TOKEN": "7:g", "BAD__BOT_TOKEN": "8:b"}}).run())
    """)
    p = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(4)
    p.send_signal(signal.SIGTERM)
    out, _ = p.communicate(timeout=20)
    assert p.returncode == 0, out
    assert "[good] TOKEN 7:g" in out                       # o'z tokeni bilan ishga tushdi
    assert out.count("[bad] to'xtadi") >= 2               # yiqilgan bot qayta ishga tushirildi
    assert "OFF__BOT_TOKEN yo'q" in out                   # tokensiz bot ishga tushirilmadi
    assert "[good] to'xtatilmoqda" in out                 # SIGTERM — bolalar ham to'xtatildi
