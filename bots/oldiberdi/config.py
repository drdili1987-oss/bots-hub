import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = os.getenv("BOT_USERNAME", "")  # "@" belgisisiz, masalan: qarz_bot

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().lstrip("-").isdigit()]

FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
# Render.com kabi muhitlarda fayl yuklash noqulay bo'lgani uchun credentials'ni
# to'liq JSON matn ko'rinishida environment variable orqali berish mumkin.
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON")
# Lokal ishlash uchun fayl yo'li (default: loyihaning ildizidagi fayl).
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")

REMINDER_INTERVAL_DAYS = int(os.getenv("REMINDER_INTERVAL_DAYS", "3"))
REMINDER_CHECK_INTERVAL_HOURS = int(os.getenv("REMINDER_CHECK_INTERVAL_HOURS", "24"))

ESKIZ_EMAIL = os.getenv("ESKIZ_EMAIL", "")
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD", "")
ESKIZ_FROM = os.getenv("ESKIZ_FROM", "4546")

SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
SMS_GATEWAY_LOGIN = os.getenv("SMS_GATEWAY_LOGIN", "")
SMS_GATEWAY_PASSWORD = os.getenv("SMS_GATEWAY_PASSWORD", "")

SMS_WEB_URL = os.getenv("SMS_WEB_URL", "https://drdili1987-oss.github.io/Qarz-oldi-berdi-bot/docs/")


TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_SESSION_STRING = os.getenv("TELEGRAM_SESSION_STRING", "")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN topilmadi. .env faylida yoki Render environment variables'da "
        "BOT_TOKEN ni sozlang."
    )

if not FIREBASE_DB_URL:
    raise RuntimeError(
        "FIREBASE_DB_URL topilmadi. .env faylida yoki Render environment "
        "variables'da FIREBASE_DB_URL ni sozlang."
    )
