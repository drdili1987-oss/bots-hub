import os
import logging

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
FIREBASE_CREDENTIALS: str = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")

_admin_ids_raw = os.getenv("ADMIN_IDS", "")
ADMIN_IDS: list[int] = [
    int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip().isdigit()
]

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring.")
if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS topilmadi. .env faylida kamida bitta admin ID kerak.")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

CURRENCIES = ("UZS", "USD")
