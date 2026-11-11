# bots-hub — 4 ta Telegram bot bitta Render Web Service (yoki Background Worker)'da

| Bot | Papka | Sozlama prefiksi |
|---|---|---|
| qarz-bot | `bots/qarz` | `QARZ__` |
| korzinka-akt-bot | `bots/korzinka` | `KORZINKA__` |
| sharbot | `bots/sharbot` | `SHARBOT__` |
| Taqvim-uzb-Bot | `bots/taqvim` | `TAQVIM__` |

`launcher.py` og'ir kutubxonalarni bir marta yuklaydi va har bir botni alohida jarayon (fork) qilib
ishga tushiradi: 4 bot ≈ 210 MB (Starter 512 MB ga bemalol sig'adi). Yiqilgan bot o'zi qayta yoqiladi,
boshqalariga ta'sir qilmaydi. Hamma bot polling rejimida ishlaydi.

## Render
- Turi: **Web Service (yoki Background Worker)**, tarif: **Starter ($7)**
- Build: `pip install -r requirements.txt`
- Start: `python launcher.py`
- `PYTHON_VERSION=3.11.9`

## Sozlamalar (Environment)
Har bir botning o'z sozlamasi prefiks bilan yoziladi; bot uni prefikssiz ko'radi va boshqa botlarning
sozlamalarini umuman ko'rmaydi.

| Bot | Kerakli sozlamalar |
|---|---|
| qarz | `QARZ__BOT_TOKEN`, `QARZ__ADMIN_IDS`, `QARZ__FIREBASE_CREDENTIALS_JSON` |
| korzinka | `KORZINKA__BOT_TOKEN`, `KORZINKA__DATABASE_URL` |
| sharbot | `SHARBOT__BOT_TOKEN`, `SHARBOT__ADMIN_ID`, `SHARBOT__XODIM_ID`, `SHARBOT__DATABASE_URL` |
| taqvim | `TAQVIM__BOT_TOKEN`, `TAQVIM__ADMIN_IDS`, `TAQVIM__FIREBASE_CREDENTIALS_JSON`, `TAQVIM__FIREBASE_DATABASE_URL` |

`<PREFIX>__BOT_TOKEN` berilmagan bot ishga tushirilmaydi — botlarni birma-bir ko'chirish mumkin.
**Muhim:** bot shu yerda yoqilgach, uning eski Render xizmatini o'chiring — bitta tokenni ikki joy
polling qilsa, Telegram «Conflict» xatosini beradi.

## Kodni o'zgartirish
Botlarning kodi endi shu repoda (`bots/<nom>`). Eski alohida repolardagi o'zgarishlar bu yerga
avtomatik o'tmaydi.

## Test
```
python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/python -m pytest -q tests
```

### oldiberdi (Qarz-oldi-berdi-bot) — prefiks `OLDIBERDI__`
Majburiy: `BOT_TOKEN`, `ADMIN_IDS`, `FIREBASE_DB_URL`, `FIREBASE_CREDENTIALS_JSON` (to'liq JSON).
Ixtiyoriy: `BOT_USERNAME`, `REMINDER_INTERVAL_DAYS`, `REMINDER_CHECK_INTERVAL_HOURS`,
`ESKIZ_EMAIL`, `ESKIZ_PASSWORD`, `ESKIZ_FROM`, `SMS_GATEWAY_URL`, `SMS_GATEWAY_LOGIN`, `SMS_GATEWAY_PASSWORD`,
`TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_SESSION_STRING`.
