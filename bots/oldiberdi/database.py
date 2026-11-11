"""
Firebase Realtime Database bilan ishlash uchun barcha funksiyalar.
Kesh (In-memory caching) bilan tezlashtirilgan.

Baza strukturasi:
    users/{user_id}   -> user_id, full_name, phone_number, username, language, created_at
    debts/{debt_id}   -> debt_id, debtor_id, creditor_id, amount, currency,
                          status ('pending'|'active'|'closed'), last_notified_at, created_at
    history/{trans_id}-> trans_id, debt_id, from_user, to_user,
                          type ('borrow'|'lend'|'income'|'outcome'),
                          amount, currency, status, timestamp
"""

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

import firebase_admin
from firebase_admin import credentials, db

from config import FIREBASE_CREDENTIALS_JSON, FIREBASE_CREDENTIALS_PATH, FIREBASE_DB_URL

logger = logging.getLogger(__name__)

TASHKENT_TZ = timezone(timedelta(hours=5))

USERS_REF = "users"
DEBTS_REF = "debts"
HISTORY_REF = "history"
FINANCE_TX_REF = "finance_transactions"
SETTINGS_REF = "settings"

def get_setting(key: str, default=None):
    try:
        ref = db.reference(f"{SETTINGS_REF}/{key}")
        val = ref.get()
        return val if val is not None else default
    except Exception as e:
        logger.warning(f"Error getting setting {key}: {e}")
        return default

def set_setting(key: str, value) -> bool:
    try:
        ref = db.reference(f"{SETTINGS_REF}/{key}")
        ref.set(value)
        return True
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")
        return False

# ==================== IN-MEMORY KESH ====================
_USERS_CACHE: dict = {}
_USERS_CACHE_TIMES: dict = {}
_USER_LANGS: dict = {}
_PHONES_CACHE: dict = {}
_USERNAMES_CACHE: dict = {}

_DEBTS_CACHE: Optional[dict] = None
_DEBTS_CACHE_TIME: float = 0.0

_HISTORY_CACHE: Optional[dict] = None
_HISTORY_CACHE_TIME: float = 0.0

_FINANCE_CACHE: Optional[dict] = None
_FINANCE_CACHE_TIME: float = 0.0

CACHE_TTL = 15.0  # Debts, Users va History uchun kesh vaqti (soniya)


def format_amount(amount) -> str:
    try:
        val = float(amount)
        if val == int(val):
            return f"{int(val):,}".replace(",", " ")
        return f"{val:,.2f}".replace(",", " ")
    except (ValueError, TypeError):
        return str(amount)


def format_date(val) -> str:
    if not val:
        return ""
    if isinstance(val, (int, float)) or (isinstance(val, str) and val.isdigit()):
        try:
            dt = datetime.fromtimestamp(float(val), tz=timezone.utc)
            return dt.strftime("%d.%m.%Y")
        except Exception:
            pass
    if isinstance(val, str):
        val_str = val.strip()
        try:
            if "T" in val_str:
                dt = datetime.fromisoformat(val_str)
                return dt.strftime("%d.%m.%Y")
            elif "-" in val_str:
                parts = val_str[:10].split("-")
                if len(parts) == 3 and len(parts[0]) == 4:
                    return f"{parts[2]}.{parts[1]}.{parts[0]}"
            elif "." in val_str:
                parts = val_str[:10].split(".")
                if len(parts) == 3 and len(parts[0]) == 4:
                    return f"{parts[2]}.{parts[1]}.{parts[0]}"
                elif len(parts) == 3 and len(parts[2]) == 4:
                    return f"{parts[0]}.{parts[1]}.{parts[2]}"
        except Exception:
            pass
    return str(val)[:10]


def parse_amount(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = re.sub(
        r"(?i)(so[\'\`\’]?m|sum|uzs|usd|\$|rub|eur|ming|k)",
        lambda m: "000" if m.group(0).lower() in ("ming", "k") else "",
        str(text),
    )
    cleaned = re.sub(r"[\s_\xa0\u202f]", "", cleaned)

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(".") > cleaned.rfind(","):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            cleaned = parts[0] + "." + parts[1]
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) == 2 and len(parts[1]) == 3 and int(parts[0]) > 0:
            cleaned = cleaned.replace(".", "")

    try:
        val = float(cleaned)
        return val if val > 0 else None
    except (ValueError, TypeError):
        return None


def _init_firebase() -> None:
    if firebase_admin._apps:
        return

    if FIREBASE_CREDENTIALS_JSON:
        cred_dict = json.loads(FIREBASE_CREDENTIALS_JSON)
        cred = credentials.Certificate(cred_dict)
    elif os.path.exists(FIREBASE_CREDENTIALS_PATH):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    else:
        raise RuntimeError(
            "Firebase credentials topilmadi. FIREBASE_CREDENTIALS_JSON "
            "(to'liq JSON matn) yoki FIREBASE_CREDENTIALS_PATH (fayl yo'li) "
            "environment variable'larini sozlang."
        )

    firebase_admin.initialize_app(cred, {"databaseURL": FIREBASE_DB_URL})


_init_firebase()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ==================== USERS ====================

def get_user(user_id: int) -> Optional[dict]:
    if not user_id:
        return None
    uid_str = str(user_id)
    now = time.time()
    if uid_str in _USERS_CACHE and (now - _USERS_CACHE_TIMES.get(uid_str, 0)) < CACHE_TTL:
        return _USERS_CACHE[uid_str]

    user_data = db.reference(f"{USERS_REF}/{uid_str}").get()
    if user_data:
        _USERS_CACHE[uid_str] = user_data
        _USERS_CACHE_TIMES[uid_str] = now
        if "language" in user_data:
            _USER_LANGS[uid_str] = user_data["language"]
        if "phone_number" in user_data:
            clean = normalize_phone(user_data["phone_number"])
            if clean:
                _PHONES_CACHE[clean] = uid_str
        if "username" in user_data and user_data["username"]:
            _USERNAMES_CACHE[user_data["username"].lstrip("@").lower()] = uid_str
    else:
        _USERS_CACHE.pop(uid_str, None)
        _USERS_CACHE_TIMES.pop(uid_str, None)
        _USER_LANGS.pop(uid_str, None)
    return user_data


def user_exists(user_id: int) -> bool:
    return get_user(user_id) is not None


def create_user(
    user_id: int,
    full_name: str,
    phone_number: str,
    language: str,
    username: str = "",
    age: int = 0,
    gender: str = "",
    country: str = "",
    city: str = "",
    occupation: str = "",
) -> None:
    uid_str = str(user_id)
    user_data = {
        "user_id": uid_str,
        "full_name": full_name,
        "phone_number": phone_number,
        "username": username or "",
        "language": language,
        "age": age,
        "gender": gender,
        "country": country,
        "city": city,
        "occupation": occupation,
        "created_at": _now_iso(),
    }
    # Keshga saqlash
    now = time.time()
    _USERS_CACHE[uid_str] = user_data
    _USERS_CACHE_TIMES[uid_str] = now
    _USER_LANGS[uid_str] = language
    clean_phone = normalize_phone(phone_number)
    if clean_phone:
        _PHONES_CACHE[clean_phone] = uid_str
    if username:
        _USERNAMES_CACHE[username.lstrip("@").lower()] = uid_str

    # Firebase'ga yozish
    db.reference(f"{USERS_REF}/{uid_str}").set(user_data)
    if username:
        db.reference(f"usernames/{username.lstrip('@').lower()}").set(uid_str)
    if clean_phone:
        db.reference(f"phones/{clean_phone}").set(uid_str)


def update_user_language(user_id: int, language: str) -> None:
    uid_str = str(user_id)
    _USER_LANGS[uid_str] = language
    if uid_str in _USERS_CACHE:
        _USERS_CACHE[uid_str]["language"] = language
    db.reference(f"{USERS_REF}/{uid_str}/language").set(language)


def delete_user(user_id: int) -> None:
    uid_str = str(user_id)
    user = _USERS_CACHE.pop(uid_str, None) or db.reference(f"{USERS_REF}/{uid_str}").get()
    _USERS_CACHE_TIMES.pop(uid_str, None)
    _USER_LANGS.pop(uid_str, None)
    if user:
        phone = normalize_phone(user.get("phone_number", ""))
        username = str(user.get("username", "")).lstrip("@").lower()
        if phone:
            _PHONES_CACHE.pop(phone, None)
            db.reference(f"phones/{phone}").delete()
        if username:
            _USERNAMES_CACHE.pop(username, None)
            db.reference(f"usernames/{username}").delete()
    db.reference(f"{USERS_REF}/{uid_str}").delete()


def get_user_language(user_id: int) -> str:
    uid_str = str(user_id)
    if uid_str in _USER_LANGS:
        return _USER_LANGS[uid_str]
    user = get_user(user_id)
    if user and "language" in user:
        lang = user["language"]
        return lang if lang in ("uz", "ru", "kk", "en") else "uz"
    return "uz"


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 9:
        digits = "998" + digits
    return digits


def find_user_by_phone(phone: str) -> Optional[dict]:
    clean = normalize_phone(phone)
    if not clean:
        return None

    if clean in _PHONES_CACHE:
        return get_user(int(_PHONES_CACHE[clean]))

    uid = db.reference(f"phones/{clean}").get()
    if uid:
        _PHONES_CACHE[clean] = str(uid)
        return get_user(int(uid))

    all_users = get_all_users()
    for uid_str, udata in all_users.items():
        if normalize_phone(udata.get("phone_number", "")) == clean:
            _PHONES_CACHE[clean] = uid_str
            return udata
    return None


def find_user_by_username(username: str) -> Optional[dict]:
    username = username.lstrip("@").lower()
    if not username:
        return None

    if username in _USERNAMES_CACHE:
        return get_user(int(_USERNAMES_CACHE[username]))

    uid = db.reference(f"usernames/{username}").get()
    if uid:
        _USERNAMES_CACHE[username] = str(uid)
        return get_user(int(uid))

    all_users = get_all_users()
    for uid_str, udata in all_users.items():
        if str(udata.get("username", "")).lower() == username:
            _USERNAMES_CACHE[username] = uid_str
            return udata
    return None


def get_all_users() -> dict:
    global _USERS_CACHE, _USERS_CACHE_TIMES
    now = time.time()
    users = db.reference(USERS_REF).get() or {}
    for uid_str, udata in users.items():
        _USERS_CACHE[uid_str] = udata
        _USERS_CACHE_TIMES[uid_str] = now
        if "language" in udata:
            _USER_LANGS[uid_str] = udata["language"]
        if "phone_number" in udata:
            clean = normalize_phone(udata["phone_number"])
            if clean:
                _PHONES_CACHE[clean] = uid_str
        if "username" in udata and udata["username"]:
            _USERNAMES_CACHE[udata["username"].lstrip("@").lower()] = uid_str
    return users


# ==================== DEBTS ====================

def get_all_debts() -> dict:
    global _DEBTS_CACHE, _DEBTS_CACHE_TIME
    now = time.time()
    if _DEBTS_CACHE is not None and (now - _DEBTS_CACHE_TIME) < CACHE_TTL:
        return _DEBTS_CACHE

    debts = db.reference(DEBTS_REF).get() or {}
    _DEBTS_CACHE = debts
    _DEBTS_CACHE_TIME = now
    return _DEBTS_CACHE


def create_debt(
    debtor_id: Optional[int],
    creditor_id: Optional[int],
    amount: float,
    currency: str,
    status: str = "pending",
    phone: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    creator_id: Optional[int] = None,
    creator_alias: Optional[str] = None,
) -> str:
    global _DEBTS_CACHE
    debt_id = str(uuid.uuid4())
    debt_data = {
        "debt_id": debt_id,
        "debtor_id": debtor_id,
        "creditor_id": creditor_id,
        "amount": amount,
        "currency": currency,
        "status": status,
        "description": description or "",
        "due_date": due_date,
        "last_notified_at": _now_iso(),
        "created_at": _now_iso(),
    }
    if phone:
        debt_data["phone"] = phone
    if creator_id is not None:
        debt_data["creator_id"] = str(creator_id)
    if creator_alias:
        debt_data["creator_alias"] = creator_alias.strip()

    if _DEBTS_CACHE is not None:
        _DEBTS_CACHE[debt_id] = debt_data

    db.reference(f"{DEBTS_REF}/{debt_id}").set(debt_data)
    return debt_id


def get_debt_party_name(debt: dict, viewer_id: int) -> str:
    """
    Qarz ko'ruvchi (viewer_id) uchun ikkinchi tomonning ko'rinadigan nomini qaytaradi.
    Agar viewer ushbu qarzni yaratuvchisi bo'lsa va o'zi uchun shaxsiy psevdonim (creator_alias)
    kiritgan bo'lsa, o'sha maxsus nomni qaytaradi.
    Aks holda (yoki ikkinchi tomon ko'rayotganda), doim ikkinchi tomonning haqiqiy ismini qaytaradi.
    Ikkinchi tomon yaratuvchi qo'ygan shaxsiy psevdonimni hech qachon ko'rmaydi.
    """
    is_creator = str(debt.get("creator_id", "")) == str(viewer_id)
    alias = debt.get("creator_alias", "").strip() if is_creator else ""

    debtor_id = debt.get("debtor_id")
    creditor_id = debt.get("creditor_id")
    phone = debt.get("phone")

    if str(debtor_id) == str(viewer_id):
        other_id = creditor_id
    elif str(creditor_id) == str(viewer_id):
        other_id = debtor_id
    else:
        other_id = debtor_id if str(debt.get("creditor_id")) == str(viewer_id) else creditor_id

    other_user = get_user(int(other_id)) if other_id else None
    real_name = other_user["full_name"] if other_user else (f"+{phone}" if phone else "Noma'lum")

    if alias:
        return alias

    return real_name


def get_debt(debt_id: str) -> Optional[dict]:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        d = dict(_DEBTS_CACHE[debt_id])
        d["debt_id"] = debt_id
        return d
    debt = db.reference(f"{DEBTS_REF}/{debt_id}").get()
    if debt:
        debt["debt_id"] = debt_id
        if _DEBTS_CACHE is not None:
            _DEBTS_CACHE[debt_id] = debt
    return debt


def update_debt_status(debt_id: str, status: str) -> None:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["status"] = status
    db.reference(f"{DEBTS_REF}/{debt_id}/status").set(status)


def update_debt_amount(debt_id: str, new_amount: float) -> None:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["amount"] = new_amount
    db.reference(f"{DEBTS_REF}/{debt_id}/amount").set(new_amount)


def update_debt_notified(debt_id: str) -> None:
    iso_now = _now_iso()
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["last_notified_at"] = iso_now
    db.reference(f"{DEBTS_REF}/{debt_id}/last_notified_at").set(iso_now)


def update_debt_notified_slot(debt_id: str, slot: str) -> None:
    iso_now = _now_iso()
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["last_notified_at"] = iso_now
        _DEBTS_CACHE[debt_id]["last_notified_slot"] = slot
    db.reference(f"{DEBTS_REF}/{debt_id}/last_notified_at").set(iso_now)
    db.reference(f"{DEBTS_REF}/{debt_id}/last_notified_slot").set(slot)



def set_debt_debtor(debt_id: str, debtor_id: int) -> None:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["debtor_id"] = debtor_id
    db.reference(f"{DEBTS_REF}/{debt_id}/debtor_id").set(debtor_id)


def set_debt_creditor(debt_id: str, creditor_id: int) -> None:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE[debt_id]["creditor_id"] = creditor_id
    db.reference(f"{DEBTS_REF}/{debt_id}/creditor_id").set(creditor_id)


def delete_debt(debt_id: str) -> None:
    if _DEBTS_CACHE is not None and debt_id in _DEBTS_CACHE:
        _DEBTS_CACHE.pop(debt_id, None)
    db.reference(f"{DEBTS_REF}/{debt_id}").delete()


def get_debts_by_debtor(user_id: int, status: Optional[str] = None) -> list:
    all_debts = get_all_debts()
    result = []
    for debt_id, d in all_debts.items():
        if str(d.get("debtor_id")) == str(user_id) and (status is None or d.get("status") == status):
            d = dict(d)
            d["debt_id"] = debt_id
            result.append(d)
    return result


def get_debts_by_creditor(user_id: int, status: Optional[str] = None) -> list:
    all_debts = get_all_debts()
    result = []
    for debt_id, d in all_debts.items():
        if str(d.get("creditor_id")) == str(user_id) and (status is None or d.get("status") == status):
            d = dict(d)
            d["debt_id"] = debt_id
            result.append(d)
    return result


# ==================== HISTORY ====================

def get_all_history() -> dict:
    global _HISTORY_CACHE, _HISTORY_CACHE_TIME
    now = time.time()
    if _HISTORY_CACHE is not None and (now - _HISTORY_CACHE_TIME) < CACHE_TTL:
        return _HISTORY_CACHE

    history = db.reference(HISTORY_REF).get() or {}
    _HISTORY_CACHE = history
    _HISTORY_CACHE_TIME = now
    return _HISTORY_CACHE


def add_history(
    debt_id: str,
    from_user: int,
    to_user: int,
    type_: str,
    amount: float,
    currency: str,
    status: str = "confirmed",
) -> str:
    global _HISTORY_CACHE
    trans_id = str(uuid.uuid4())
    data = {
        "trans_id": trans_id,
        "debt_id": debt_id,
        "from_user": str(from_user),
        "to_user": str(to_user),
        "type": type_,
        "amount": amount,
        "currency": currency,
        "status": status,
        "timestamp": _now_iso(),
    }
    if _HISTORY_CACHE is not None:
        _HISTORY_CACHE[trans_id] = data

    db.reference(f"{HISTORY_REF}/{trans_id}").set(data)
    return trans_id


def get_history_by_user(user_id: int) -> list:
    all_history = get_all_history()
    result = []
    uid_str = str(user_id)
    for trans_id, h in all_history.items():
        if str(h.get("from_user")) == uid_str or str(h.get("to_user")) == uid_str:
            h = dict(h)
            h["trans_id"] = trans_id
            result.append(h)
    result.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return result


# ==================== ADMIN STATISTIKA ====================

def get_stats() -> dict:
    users = get_all_users()
    debts = get_all_debts()

    male_count = 0
    female_count = 0
    countries = {}
    cities = {}
    occupations = {}

    for u in users.values():
        g = u.get("gender", "").lower()
        if g in ["erkak", "мужской", "еркек", "male"]:
            male_count += 1
        elif g in ["ayol", "женский", "әйел", "female"]:
            female_count += 1

        c = u.get("country", "").strip().title()
        if c:
            countries[c] = countries.get(c, 0) + 1

        city = u.get("city", "").strip().title()
        if city:
            cities[city] = cities.get(city, 0) + 1

        occ = u.get("occupation", "").strip().title()
        if occ:
            occupations[occ] = occupations.get(occ, 0) + 1

    top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
    top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
    top_occupations = sorted(occupations.items(), key=lambda x: x[1], reverse=True)[:5]

    active_debts = [d for d in debts.values() if d.get("status") == "active"]
    total_uzs = sum(float(d.get("amount", 0)) for d in active_debts if d.get("currency") == "UZS")
    total_usd = sum(float(d.get("amount", 0)) for d in active_debts if d.get("currency") == "USD")

    return {
        "total_users": len(users),
        "male_count": male_count,
        "female_count": female_count,
        "top_countries": top_countries,
        "top_cities": top_cities,
        "top_occupations": top_occupations,
        "active_debts_count": len(active_debts),
        "total_uzs": total_uzs,
        "total_usd": total_usd,
    }


# ==================== SHAXSIY MOLIYA (PERSONAL FINANCE) ====================

DEFAULT_CATEGORIES = [
    "🍽 Oziq-ovqat",
    "🚖 Transport",
    "☕️ Kafe / Restoran",
    "💡 Kommunal & Uy",
    "💼 Oylik / Maosh",
    "🏢 Biznes & Savdo",
    "👕 Kiyim-kechak",
    "💊 Sog'liq & Tibbiyot",
    "📱 Aloqa & Internet",
    "🎁 Sovg'a & Bayram",
    "📦 Boshqa",
]

CATEGORY_KEYWORDS = {
    "🍽 Oziq-ovqat": ["bozor", "bozorlik", "ovqat", "non", "gosht", "go'sht", "supermarket", "korzinka", "makro", "magazin", "produkt", "oziq", "bazar", "eda", "sabzavot", "meva"],
    "🚖 Transport": ["taksi", "taxi", "yandex", "benzin", "metro", "avtobus", "marshrutka", "zapravka", "propan", "metan", "moy", "doroga", "proyezd", "avto", "zapchast"],
    "☕️ Kafe / Restoran": ["kafe", "restoran", "obed", "tushlik", "nonushta", "kofe", "coffee", "choyxona", "lavash", "burger", "fastfood", "pitsa", "pizza", "choy"],
    "💡 Kommunal & Uy": ["kommunal", "svet", "gaz", "suv", "musor", "kvartplata", "ijara", "domoy", "arenda", "remont", "uy", "mebel"],
    "💼 Oylik / Maosh": ["oylik", "maosh", "avans", "zarplata", "salary", "ish haqi", "premiya"],
    "🏢 Biznes & Savdo": ["biznes", "savdo", "tovar", "klient", "foyda", "kassa", "daromad", "invest"],
    "👕 Kiyim-kechak": ["kiyim", "shim", "kofta", "poyabzal", "tufli", "krossovka", "kurtka", "shopping", "odejda", "libos"],
    "💊 Sog'liq & Tibbiyot": ["apteka", "dori", "shifokor", "vrach", "analiz", "stomatolog", "klinika", "lecheniye", "tibbiyot", "massaj"],
    "📱 Aloqa & Internet": ["telefon", "internet", "payme", "click", "uztelecom", "beeline", "ucell", "mobiuz", "svyaz", "tarif", "wi-fi", "wifi"],
    "🎁 Sovg'a & Bayram": ["sovga", "sovg'a", "hadya", "bonus", "mukofot", "toy", "to'y", "ehson", "podarok", "bayram", "tug'ilgan kun"],
}


def get_default_categories() -> list:
    return list(DEFAULT_CATEGORIES)


def get_all_finance_transactions() -> dict:
    global _FINANCE_CACHE, _FINANCE_CACHE_TIME
    _init_firebase()
    now = time.time()
    if _FINANCE_CACHE is not None and (now - _FINANCE_CACHE_TIME) < CACHE_TTL:
        return _FINANCE_CACHE

    val = db.reference(FINANCE_TX_REF).get()
    _FINANCE_CACHE = val if val else {}
    _FINANCE_CACHE_TIME = now
    return _FINANCE_CACHE


def add_finance_transaction(
    user_id: int,
    type_: str,  # "income" or "expense"
    amount: float,
    currency: str = "UZS",
    category: str = "📦 Boshqa",
    note: str = "",
    date_str: Optional[str] = None,
) -> str:
    global _FINANCE_CACHE
    _init_firebase()
    tx_id = str(uuid.uuid4())

    now_tashkent = datetime.now(TASHKENT_TZ)
    if not date_str:
        date_str = now_tashkent.strftime("%d.%m.%Y")
    else:
        date_str = format_date(date_str)

    data = {
        "tx_id": tx_id,
        "user_id": int(user_id),
        "type": type_,
        "amount": float(amount),
        "currency": currency.upper(),
        "category": category.strip() if category else "📦 Boshqa",
        "note": note.strip() if note else "",
        "date": date_str,
        "created_at": _now_iso(),
        "timestamp": time.time(),
    }

    if _FINANCE_CACHE is not None:
        _FINANCE_CACHE[tx_id] = data

    db.reference(f"{FINANCE_TX_REF}/{tx_id}").set(data)
    return tx_id


def get_user_finance_transactions(user_id: int, period: str = "all") -> list:
    """
    period: 'today', 'week', 'month', 'all'
    """
    all_tx = get_all_finance_transactions()
    uid = int(user_id)
    now_tashkent = datetime.now(TASHKENT_TZ)
    today_str = now_tashkent.strftime("%d.%m.%Y")
    current_month_str = now_tashkent.strftime(".%m.%Y")
    
    # Week range (start of week - Monday)
    start_of_week = now_tashkent - timedelta(days=now_tashkent.weekday())
    start_of_week_date = start_of_week.date()

    result = []
    for tx_id, tx in all_tx.items():
        if int(tx.get("user_id", 0)) == uid:
            item = dict(tx)
            item["tx_id"] = tx_id
            t_date_str = item.get("date", "")
            
            # Period filter
            if period == "today":
                if t_date_str != today_str:
                    continue
            elif period == "month":
                if not t_date_str.endswith(current_month_str):
                    continue
            elif period == "week":
                try:
                    parts = t_date_str.split(".")
                    if len(parts) == 3:
                        d = datetime(int(parts[2]), int(parts[1]), int(parts[0])).date()
                        if d < start_of_week_date:
                            continue
                except Exception:
                    pass

            result.append(item)

    # Sort by timestamp / created_at descending (eng yangi yozuvlar oldinda)
    result.sort(key=lambda x: (str(x.get("date", "")), float(x.get("timestamp", 0))), reverse=True)
    return result


def get_finance_transaction(tx_id: str) -> Optional[dict]:
    all_tx = get_all_finance_transactions()
    tx = all_tx.get(tx_id)
    if tx:
        res = dict(tx)
        res["tx_id"] = tx_id
        return res
    _init_firebase()
    val = db.reference(f"{FINANCE_TX_REF}/{tx_id}").get()
    if val:
        val["tx_id"] = tx_id
    return val


def update_finance_transaction(tx_id: str, **kwargs) -> bool:
    global _FINANCE_CACHE
    _init_firebase()
    ref = db.reference(f"{FINANCE_TX_REF}/{tx_id}")
    current = ref.get()
    if not current:
        return False

    for k, v in kwargs.items():
        current[k] = v

    ref.update(kwargs)
    if _FINANCE_CACHE is not None:
        if tx_id in _FINANCE_CACHE:
            _FINANCE_CACHE[tx_id].update(kwargs)
        else:
            _FINANCE_CACHE[tx_id] = current
    return True


def delete_finance_transaction(tx_id: str) -> bool:
    global _FINANCE_CACHE
    _init_firebase()
    db.reference(f"{FINANCE_TX_REF}/{tx_id}").delete()
    if _FINANCE_CACHE is not None and tx_id in _FINANCE_CACHE:
        del _FINANCE_CACHE[tx_id]
    return True


def get_finance_balance(user_id: int, period: str = "month") -> dict:
    """
    Returns aggregated income, expense, balance per currency and category breakdown.
    """
    txs = get_user_finance_transactions(user_id, period=period)
    
    uzs_income = 0.0
    uzs_expense = 0.0
    usd_income = 0.0
    usd_expense = 0.0

    categories_uzs = {}
    categories_usd = {}
    max_expense_uzs = {"amount": 0.0, "note": "", "date": "", "category": ""}
    max_expense_usd = {"amount": 0.0, "note": "", "date": "", "category": ""}

    for tx in txs:
        amt = float(tx.get("amount", 0))
        curr = tx.get("currency", "UZS")
        tx_type = tx.get("type", "expense")
        cat = tx.get("category", "📦 Boshqa")
        note = tx.get("note", "")
        dt = tx.get("date", "")

        if curr == "USD":
            if tx_type == "income":
                usd_income += amt
            else:
                usd_expense += amt
                categories_usd[cat] = categories_usd.get(cat, 0.0) + amt
                if amt > max_expense_usd["amount"]:
                    max_expense_usd = {"amount": amt, "note": note, "date": dt, "category": cat}
        else:
            if tx_type == "income":
                uzs_income += amt
            else:
                uzs_expense += amt
                categories_uzs[cat] = categories_uzs.get(cat, 0.0) + amt
                if amt > max_expense_uzs["amount"]:
                    max_expense_uzs = {"amount": amt, "note": note, "date": dt, "category": cat}

    return {
        "period": period,
        "total_count": len(txs),
        "UZS": {
            "income": uzs_income,
            "expense": uzs_expense,
            "balance": uzs_income - uzs_expense,
            "categories": categories_uzs,
            "max_expense": max_expense_uzs if max_expense_uzs["amount"] > 0 else None,
        },
        "USD": {
            "income": usd_income,
            "expense": usd_expense,
            "balance": usd_income - usd_expense,
            "categories": categories_usd,
            "max_expense": max_expense_usd if max_expense_usd["amount"] > 0 else None,
        },
    }


def parse_quick_finance(text: str) -> Optional[dict]:
    if not text:
        return None
    raw = text.strip()

    # 0. Telefon raqamlari (masalan: +998901234567, 998935991007, +998 90 123 45 67) moliyaviy tranzaksiya sifatida olinmasin
    clean_digits = re.sub(r"\D", "", raw)
    has_finance_keyword = bool(re.search(r"\b(so[\'\`\’]?m|sum|uzs|usd|\$|rub|eur|k|ming|mln|million)\b", raw, re.IGNORECASE))
    if len(clean_digits) in (9, 12) and not has_finance_keyword:
        if clean_digits.startswith("998") or len(clean_digits) == 9:
            return None

    # 1. Determine type (+ or -)
    tx_type = None
    if raw.startswith("+"):
        tx_type = "income"
        raw = raw[1:].strip()
    elif raw.startswith("-"):
        tx_type = "expense"
        raw = raw[1:].strip()

    # 2. Currency check
    currency = "UZS"
    if "$" in raw or re.search(r"\b(usd|dollar)\b", raw, re.IGNORECASE):
        currency = "USD"

    # 3. Extract amount part
    match = re.search(
        r"(\d+(?:[\s_.,]\d+)*(?:\s*(?:k|ming|mln|m|million|usd|\$|so[\'\`\’]?m|sum|uzs))?)",
        raw,
        re.IGNORECASE,
    )
    if not match:
        return None
    amount_str = match.group(1)
    note_part = (raw[:match.start()] + " " + raw[match.end():]).strip()

    # Clean amount
    cleaned = re.sub(r"(so[\'\`\’]?m|sum|uzs|usd|\$|rub|eur)", "", amount_str, flags=re.IGNORECASE)

    # If 2.5 mln or 1.5 k
    if re.search(r"\d+\.\d+\s*(mln|million|m)", cleaned, re.IGNORECASE):
        m = re.search(r"(\d+\.\d+)\s*(mln|million|m)", cleaned, re.IGNORECASE)
        cleaned = str(int(float(m.group(1)) * 1_000_000))
    elif re.search(r"\d+\.\d+\s*(ming|k)", cleaned, re.IGNORECASE):
        m = re.search(r"(\d+\.\d+)\s*(ming|k)", cleaned, re.IGNORECASE)
        cleaned = str(int(float(m.group(1)) * 1_000))
    else:
        cleaned = re.sub(r"(ming|k)\b", "000", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"(mln|million|m)\b", "000000", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"[\s_\xa0\u202f]", "", cleaned)

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(".") > cleaned.rfind(","):
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            cleaned = parts[0] + "." + parts[1]
        else:
            cleaned = cleaned.replace(",", "")

    try:
        amount = float(cleaned)
        if amount <= 0 or amount >= 100_000_000_000:
            return None
    except Exception:
        return None

    # If type not explicitly +/-:
    if not tx_type:
        lower_note = note_part.lower()
        if any(w in lower_note for w in ["oylik", "maosh", "avans", "zarplata", "daromad", "bonus", "tushum", "daromad"]):
            tx_type = "income"
        else:
            tx_type = "expense"

    # Category detection
    lower_note = note_part.lower()
    detected_cat = "📦 Boshqa"
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower_note for kw in keywords):
            detected_cat = cat
            break

    if detected_cat == "📦 Boshqa" and tx_type == "income":
        detected_cat = "💼 Oylik / Maosh"

    now_tashkent = datetime.now(TASHKENT_TZ)
    date_str = now_tashkent.strftime("%d.%m.%Y")

    return {
        "type": tx_type,
        "amount": amount,
        "currency": currency,
        "category": detected_cat,
        "note": note_part,
        "date": date_str,
    }


def get_user_debts_summary(user_id: int) -> dict:
    all_debts = get_all_debts()
    uid_str = str(user_id)

    lent_active_uzs = 0.0
    lent_active_usd = 0.0
    lent_active_count = 0
    lent_active_items = []

    borrowed_active_uzs = 0.0
    borrowed_active_usd = 0.0
    borrowed_active_count = 0
    borrowed_active_items = []

    lent_closed_count = 0
    borrowed_closed_count = 0

    for d in all_debts.values():
        c_id = str(d.get("creditor_id", ""))
        d_id = str(d.get("debtor_id", ""))
        status = d.get("status", "")
        amt = float(d.get("amount", 0))
        curr = d.get("currency", "UZS")

        # Men bergan qarz (men creditor bo'lgan) -> debtors
        if c_id == uid_str:
            if status == "active":
                lent_active_count += 1
                if curr == "USD":
                    lent_active_usd += amt
                else:
                    lent_active_uzs += amt
                lent_active_items.append(d)
            elif status == "closed":
                lent_closed_count += 1

        # Men olgan qarz (men debtor bo'lgan) -> creditors
        if d_id == uid_str:
            if status == "active":
                borrowed_active_count += 1
                if curr == "USD":
                    borrowed_active_usd += amt
                else:
                    borrowed_active_uzs += amt
                borrowed_active_items.append(d)
            elif status == "closed":
                borrowed_closed_count += 1

    # Sort largest debtors and creditors
    lent_active_items.sort(key=lambda x: float(x.get("amount", 0)), reverse=True)
    borrowed_active_items.sort(key=lambda x: float(x.get("amount", 0)), reverse=True)

    return {
        "lent": {
            "active_count": lent_active_count,
            "closed_count": lent_closed_count,
            "uzs": lent_active_uzs,
            "usd": lent_active_usd,
            "top_items": lent_active_items[:5],
        },
        "borrowed": {
            "active_count": borrowed_active_count,
            "closed_count": borrowed_closed_count,
            "uzs": borrowed_active_uzs,
            "usd": borrowed_active_usd,
            "top_items": borrowed_active_items[:5],
        },
        "net_uzs": lent_active_uzs - borrowed_active_uzs,
        "net_usd": lent_active_usd - borrowed_active_usd,
    }


def get_comprehensive_financial_report(user_id: int, period: str = "month") -> dict:
    fin = get_finance_balance(user_id, period=period)
    debts = get_user_debts_summary(user_id)

    # Calculate estimated total net worth in UZS and USD
    uzs_wallet = fin["UZS"]["balance"]
    usd_wallet = fin["USD"]["balance"]

    uzs_lent = debts["lent"]["uzs"]
    usd_lent = debts["lent"]["usd"]

    uzs_borrowed = debts["borrowed"]["uzs"]
    usd_borrowed = debts["borrowed"]["usd"]

    # Sof aktivlar (Hamyon qoldig'i + Kutilayotgan qarzlar - To'lanishi kerak qarzlar)
    uzs_net_worth = uzs_wallet + uzs_lent - uzs_borrowed
    usd_net_worth = usd_wallet + usd_lent - usd_borrowed

    return {
        "period": period,
        "finance": fin,
        "debts": debts,
        "net_worth": {
            "UZS": uzs_net_worth,
            "USD": usd_net_worth,
        },
    }


