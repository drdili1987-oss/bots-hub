import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# --- Admin foydalanuvchilar ---
# O'z Telegram ID'ingizni shu ro'yxatga qo'shing.
# ID'ingizni bilish uchun botga /myid buyrug'ini yuboring.
ADMIN_IDS: list[int] = [156664]

# --- Ijrochi (xizmat ko'rsatuvchi) rekvizitlari ---
# Bu ma'lumotlar har bir akt hujjatida "Ijrochi" sifatida chiqadi.
COMPANY_NAME = "YATT Rustamov Dilmurod"
COMPANY_ADDRESS = "Bektemir tumani, Nurli ko'chasi"
COMPANY_PHONE = "+998 97 777 43 11"

# --- Buyurtmachi (doimiy mijoz) nomi ---
# Har bir aktda do'kon kodi va manzili alohida so'raladi, bu esa tarmoq nomi.
CLIENT_NAME = "\"Korzinka\" savdo tarmog'i"

# --- Narxlar (so'mda) ---
# Narxlar o'zgarsa, faqat shu yerni tahrirlang, boshqa joyga tegmang.
PRICES = {
    "karnay_shahar": 3_000_000,      # Karnay-surnay, shahar
    "karnay_viloyat": 3_600_000,     # Karnay-surnay, viloyat
    "shar_arka_per_metr": 150_000,   # Shar arka, 1 metr narxi
    "shar_logo_per_dona": 12_000,    # Shar logotip, 1 dona narxi
    "dj": 2_200_000,                 # DJ, belgilangan narx
    "animator_per_dona": 600_000,    # Animator, 1 dona narxi
    "boshlovchi": 800_000,           # Boshlovchi, belgilangan narx
    "transport_per_km": 3_000,       # Transport, 1 km narxi
    "raqqosa_per_dona": 750_000,     # Raqqosa, 1 dona narxi
}

# --- Tan narxlar / Xarajatlar (so'mda) ---
# Har bir xizmat uchun siz to'laydigan xarajat summasi
COST_PRICES = {
    "karnay_shahar": 2_700_000,      # 1. Karnay shahar tan narxi
    "karnay_viloyat": 3_000_000,     # 2. Karnay viloyat tan narxi
    "shar_arka_per_metr": 120_000,   # 3. Shar arka 1 metr tan narxi
    "shar_logo_per_dona": 12_000,    # 4. Shar logo 1 dona tan narxi
    "dj": 1_000_000,                 # 5. DJ tan narxi
    "animator_per_dona": 250_000,    # 6. Animator 1 dona tan narxi
    "boshlovchi": 500_000,           # 7. Boshlovchi tan narxi
    "transport_fixed": 200_000,      # 8. Transport xarajati (belgilangan)
    "transport_per_km": 2_000,       # 8. Transport 1 km tan narxi
    "raqqosa_per_dona": 500_000,     # 9. Raqqosa 1 dona tan narxi
}
