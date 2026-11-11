"""
Baza qatlami:
- FIREBASE_CREDENTIALS muhit o`zgaruvchisi yoki fayli bo`lsa -> Firebase Firestore
- Aks holda -> lokal SQLite (qarz_bot.db)
"""
from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import config

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Qaysi baza ishlatilishini aniqlash
# ------------------------------------------------------------------ #
_USE_FIREBASE = bool(os.getenv("FIREBASE_CREDENTIALS") or os.getenv("FIREBASE_CREDENTIALS_JSON") or os.path.exists(config.FIREBASE_CREDENTIALS))

# Firebase uchun
_fb_app  = None
_fb_db   = None

# SQLite uchun
_sq_conn: Optional[sqlite3.Connection] = None
DB_PATH  = "qarz_bot.db"


# ================================================================== #
#  INIT
# ================================================================== #

def _init_firebase_backend() -> None:
    global _fb_app, _fb_db
    import firebase_admin
    from firebase_admin import credentials, firestore

    cred_path = config.FIREBASE_CREDENTIALS
    # Render da JSON mazmuni env var sifatida berilishi mumkin
    json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if json_env:
        import json, tempfile, base64
        json_env = json_env.strip("`'\" \n\r\t")
        if not json_env.startswith('{'):
            try:
                json_env = base64.b64decode(json_env).decode('utf-8')
            except Exception as e:
                raise RuntimeError(f"Base64 parse error: {e}, string starts with {json_env[:10]}")
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        tmp.write(json_env)
        tmp.close()
        cred_path = tmp.name

    cred = credentials.Certificate(cred_path)
    _fb_app = firebase_admin.initialize_app(cred)
    _fb_db  = firestore.client()
    logger.info("Firebase Firestore ulandi.")


def _init_sqlite_backend() -> None:
    global _sq_conn
    _sq_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    _sq_conn.row_factory = sqlite3.Row
    _sq_conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id     INTEGER PRIMARY KEY,
            full_name   TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'employee',
            balance_uzs REAL    NOT NULL DEFAULT 0,
            balance_usd REAL    NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            user_id        INTEGER NOT NULL,
            type           TEXT    NOT NULL,
            currency       TEXT    NOT NULL,
            amount         REAL    NOT NULL,
            status         TEXT    NOT NULL DEFAULT 'pending',
            created_by     TEXT    NOT NULL,
            timestamp      TEXT    NOT NULL
        );
    """)
    _sq_conn.commit()
    logger.info("SQLite baza ishga tushdi: %s", DB_PATH)


def init_firebase() -> None:
    """Dastur boshida bir marta chaqiriladi."""
    if _USE_FIREBASE:
        try:
            _init_firebase_backend()
            return
        except Exception as e:
            logger.warning("Firebase ulanmadi (%s), SQLite ishlatiladi.", e)
            if os.getenv("FIREBASE_CREDENTIALS_JSON"):
                raise RuntimeError(f"Firebase failed to init! {e}")
    _init_sqlite_backend()


# ================================================================== #
#  FIREBASE IMPLEMENTATIONS
# ================================================================== #

def _fb_get_user(user_id: int) -> Optional[dict]:
    from google.cloud.firestore_v1 import Increment as _Inc
    doc = _fb_db.collection("users").document(str(user_id)).get()
    if not doc.exists:
        return None
    d = doc.to_dict(); d["user_id"] = user_id; return d


def _fb_create_user(user_id: int, full_name: str, role: str) -> dict:
    data = {"full_name": full_name, "role": role, "balance_uzs": 0, "balance_usd": 0}
    _fb_db.collection("users").document(str(user_id)).set(data)
    return {**data, "user_id": user_id}


def _fb_get_all_employees() -> list:
    docs = _fb_db.collection("users").where("role", "==", "employee").stream()
    result = []
    for doc in docs:
        d = doc.to_dict(); d["user_id"] = int(doc.id); result.append(d)
    result.sort(key=lambda u: u.get("full_name", ""))
    return result


def _fb_update_balance(user_id: int, currency: str, delta: float) -> None:
    from google.cloud.firestore_v1 import Increment
    field = "balance_uzs" if currency == "UZS" else "balance_usd"
    _fb_db.collection("users").document(str(user_id)).update({field: Increment(delta)})


def _fb_add_tx(user_id, tx_type, currency, amount, status, created_by) -> str:
    from firebase_admin import firestore as _fs
    tx_id = str(uuid.uuid4())
    _fb_db.collection("transactions").document(tx_id).set({
        "user_id": user_id, "type": tx_type, "currency": currency,
        "amount": amount, "status": status, "created_by": created_by,
        "timestamp": _fs.SERVER_TIMESTAMP,
    })
    return tx_id


def _fb_update_tx_status(tx_id: str, status: str) -> None:
    _fb_db.collection("transactions").document(tx_id).update({"status": status})


def _fb_get_tx(tx_id: str) -> Optional[dict]:
    doc = _fb_db.collection("transactions").document(tx_id).get()
    if not doc.exists: return None
    d = doc.to_dict(); d["transaction_id"] = tx_id; return d


def _fb_get_user_txs(user_id: int, limit: int) -> list:
    docs = _fb_db.collection("transactions").where("user_id", "==", user_id).stream()
    result = [{**doc.to_dict(), "transaction_id": doc.id} for doc in docs]
    result.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return result[:limit]


def _fb_get_all_txs(limit: int) -> list:
    from google.cloud.firestore_v1 import Query
    docs = (
        _fb_db.collection("transactions")
        .order_by("timestamp", direction=Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [{**doc.to_dict(), "transaction_id": doc.id} for doc in docs]


# ================================================================== #
#  SQLITE IMPLEMENTATIONS
# ================================================================== #

def _sq() -> sqlite3.Connection:
    if _sq_conn is None:
        raise RuntimeError("SQLite ulanmagan.")
    return _sq_conn


def _sq_get_user(user_id: int) -> Optional[dict]:
    cur = _sq().cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone(); return dict(row) if row else None


def _sq_create_user(user_id: int, full_name: str, role: str) -> dict:
    _sq().execute(
        "INSERT OR IGNORE INTO users (user_id,full_name,role,balance_uzs,balance_usd) VALUES(?,?,?,0,0)",
        (user_id, full_name, role),
    ); _sq().commit()
    return {"user_id": user_id, "full_name": full_name, "role": role, "balance_uzs": 0.0, "balance_usd": 0.0}


def _sq_get_all_employees() -> list:
    cur = _sq().cursor()
    cur.execute("SELECT * FROM users WHERE role='employee' ORDER BY full_name")
    return [dict(r) for r in cur.fetchall()]


def _sq_update_balance(user_id: int, currency: str, delta: float) -> None:
    field = "balance_uzs" if currency == "UZS" else "balance_usd"
    _sq().execute(f"UPDATE users SET {field}={field}+? WHERE user_id=?", (delta, user_id))
    _sq().commit()


def _sq_add_tx(user_id, tx_type, currency, amount, status, created_by) -> str:
    tx_id = str(uuid.uuid4())
    ts = datetime.now(timezone.utc).isoformat()
    _sq().execute(
        "INSERT INTO transactions VALUES(?,?,?,?,?,?,?,?)",
        (tx_id, user_id, tx_type, currency, amount, status, created_by, ts),
    ); _sq().commit()
    return tx_id


def _sq_update_tx_status(tx_id: str, status: str) -> None:
    _sq().execute("UPDATE transactions SET status=? WHERE transaction_id=?", (status, tx_id))
    _sq().commit()


def _sq_get_tx(tx_id: str) -> Optional[dict]:
    cur = _sq().cursor()
    cur.execute("SELECT * FROM transactions WHERE transaction_id=?", (tx_id,))
    row = cur.fetchone(); return dict(row) if row else None


def _sq_get_user_txs(user_id: int, limit: int) -> list:
    cur = _sq().cursor()
    cur.execute("SELECT * FROM transactions WHERE user_id=? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
    return [dict(r) for r in cur.fetchall()]


def _sq_get_all_txs(limit: int) -> list:
    cur = _sq().cursor()
    cur.execute("SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,))
    return [dict(r) for r in cur.fetchall()]


# ================================================================== #
#  PUBLIC ASYNC API  (bir xil interfeys - Firebase yoki SQLite)
# ================================================================== #

def _use_fb() -> bool:
    return _fb_db is not None


async def get_user(user_id: int) -> Optional[dict]:
    fn = _fb_get_user if _use_fb() else _sq_get_user
    return await asyncio.to_thread(fn, user_id)


async def get_or_create_user(user_id: int, full_name: str, role: str = "employee") -> dict:
    user = await get_user(user_id)
    if user: return user
    fn = _fb_create_user if _use_fb() else _sq_create_user
    return await asyncio.to_thread(fn, user_id, full_name, role)


async def get_all_employees() -> list:
    fn = _fb_get_all_employees if _use_fb() else _sq_get_all_employees
    return await asyncio.to_thread(fn)


async def update_balance(user_id: int, currency: str, delta: float) -> None:
    fn = _fb_update_balance if _use_fb() else _sq_update_balance
    await asyncio.to_thread(fn, user_id, currency, delta)


async def add_transaction(user_id, tx_type, currency, amount, status, created_by) -> str:
    fn = _fb_add_tx if _use_fb() else _sq_add_tx
    return await asyncio.to_thread(fn, user_id, tx_type, currency, amount, status, created_by)


async def update_transaction_status(tx_id: str, status: str) -> None:
    fn = _fb_update_tx_status if _use_fb() else _sq_update_tx_status
    await asyncio.to_thread(fn, tx_id, status)


async def get_transaction(tx_id: str) -> Optional[dict]:
    fn = _fb_get_tx if _use_fb() else _sq_get_tx
    return await asyncio.to_thread(fn, tx_id)


async def get_user_transactions(user_id: int, limit: int = 20) -> list:
    fn = _fb_get_user_txs if _use_fb() else _sq_get_user_txs
    return await asyncio.to_thread(fn, user_id, limit)


async def get_all_transactions(limit: int = 50) -> list:
    fn = _fb_get_all_txs if _use_fb() else _sq_get_all_txs
    return await asyncio.to_thread(fn, limit)
