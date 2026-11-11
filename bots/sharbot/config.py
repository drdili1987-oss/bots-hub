import os
from dotenv import load_dotenv

load_dotenv()

# Telegram bot tokenini @BotFather dan oling va .env faylga yozing
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Sizning (admin) Telegram user ID raqamingiz.
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Narxlar (so'mda)
ARKA_NARXI_METR = 120_000       # 1 metr shar arka narxi
LOGOTIP_NARXI_DONA = 11_000     # 1 dona shar logotip narxi
TRANSPORT_NARXI_KM = 2_000      # 1 km transport narxi

DB_PATH = os.getenv("DB_PATH", "sharbot.db")
DATABASE_URL = os.getenv("DATABASE_URL")
XODIM_ID = int(os.getenv("XODIM_ID", "0"))
