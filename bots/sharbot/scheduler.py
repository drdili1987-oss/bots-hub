import asyncio
import logging
import re
from datetime import datetime, date, timedelta, timezone
from config import ADMIN_ID, XODIM_ID
import database as db

# Setup logging
logger = logging.getLogger("scheduler")

# O'zbekiston vaqti (UTC+5)
UZT = timezone(timedelta(hours=5))

async def send_tomorrow_notifications(bot):
    logger.info("Running send_tomorrow_notifications job...")
    uzt_now = datetime.now(UZT)
    tomorrow = (uzt_now + timedelta(days=1)).date()

    # Fetch all active pending orders
    orders = await db.get_orders_by_statuses(['yuborilgan', 'qabul_qilingan'])

    # Group orders by worker, and collect all tomorrow orders
    worker_orders = {}
    tomorrow_orders_all = []

    for o in orders:
        sana_str = o.get("sana", "").strip()
        sana_str = re.sub(r'[\s\-/]+', '.', sana_str)

        parsed_date = None
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y.%m.%d", "%d.%m"):
            try:
                if fmt == "%d.%m":
                    parsed_date = datetime.strptime(sana_str, fmt).date().replace(year=tomorrow.year)
                else:
                    parsed_date = datetime.strptime(sana_str, fmt).date()
                break
            except ValueError:
                continue

        if parsed_date is None:
            parts = [int(p) for p in re.findall(r'\d+', sana_str)]
            if len(parts) == 3:
                if parts[0] > 1000:
                    parsed_date = date(parts[0], parts[1], parts[2])
                else:
                    year = parts[2]
                    if year < 100:
                        year += 2000
                    parsed_date = date(year, parts[1], parts[0])
            elif len(parts) == 2:
                parsed_date = date(tomorrow.year, parts[1], parts[0])

        if parsed_date == tomorrow:
            worker_id = o["worker_id"]
            if worker_id not in worker_orders:
                worker_orders[worker_id] = []
            worker_orders[worker_id].append(o)
            tomorrow_orders_all.append(o)

    # --- SHARCHIlarga xabar ---
    for worker_id, orders_list in worker_orders.items():
        worker = await db.get_worker_by_id(worker_id)
        if not worker:
            continue

        lines = [
            f"🔔 Eslatma! Ertaga ({tomorrow.strftime('%d.%m.%Y')}) sizda {len(orders_list)} ta buyurtma bor:\n"
        ]
        for i, o in enumerate(orders_list, 1):
            lines.append(
                f"{i}. 🏪 Magazin: {o['magazin_kodi']}\n"
                f"   📍 Manzil: {o['manzil']}\n"
                f"   📐 Taxminiy arka: {o.get('arka_metr', 0)} metr\n"
                f"   🔴 Qizil: {o.get('qizil', 0)} dona  ⚪ Oq: {o.get('oq', 0)} dona\n"
                f"   🟠 Orange: {o.get('orange', 0)} dona  🟡 Sariq: {o.get('sariq', 0)} dona\n"
            )

        text = "\n".join(lines)
        try:
            await bot.send_message(worker["tg_id"], text)
            logger.info(f"Sent tomorrow reminder to worker {worker['ism']} (ID: {worker['tg_id']})")
        except Exception as e:
            logger.error(f"Failed to send reminder to worker {worker['ism']}: {e}")

    # --- ADMIN va XODIM ga xabar ---
    if tomorrow_orders_all:
        admin_lines = [
            f"📋 Ertangi buyurtmalar eslatmasi ({tomorrow.strftime('%d.%m.%Y')}):\n"
            f"Jami: {len(tomorrow_orders_all)} ta buyurtma\n"
        ]
        for i, o in enumerate(tomorrow_orders_all, 1):
            worker = await db.get_worker_by_id(o["worker_id"])
            wname = worker["ism"] if worker else "?"
            admin_lines.append(
                f"\n{i}. 🏪 Magazin: {o['magazin_kodi']}\n"
                f"   📍 Manzil: {o['manzil']}\n"
                f"   📐 Arka: {o.get('arka_metr', 0)} metr\n"
                f"   🔴 {o.get('qizil', 0)}  ⚪ {o.get('oq', 0)}  🟠 {o.get('orange', 0)}  🟡 {o.get('sariq', 0)}\n"
                f"   👤 Sharchi: {wname}"
            )

        admin_text = "\n".join(admin_lines)

        # Adminga yuborish
        try:
            await bot.send_message(ADMIN_ID, admin_text)
            logger.info("Sent tomorrow reminder to Admin")
        except Exception as e:
            logger.error(f"Failed to send reminder to Admin: {e}")

        # Xodimga yuborish
        try:
            await bot.send_message(XODIM_ID, admin_text)
            logger.info("Sent tomorrow reminder to Xodim")
        except Exception as e:
            logger.error(f"Failed to send reminder to Xodim: {e}")

    else:
        # Ertaga buyurtma yo'q — hech kimga xabar yuborilmaydi
        logger.info(f"No orders for tomorrow ({tomorrow.strftime('%d.%m.%Y')}) — no notifications sent.")


async def daily_scheduler(bot):
    logger.info("Daily reminder scheduler started.")
    while True:
        now = datetime.now(UZT)
        # Har kuni soat 19:00 da ishga tushadi (O'zbekiston vaqti bo'yicha)
        target = now.replace(hour=19, minute=0, second=0, microsecond=0)
        if now >= target:
            # 19:00 o'tib ketgan bo'lsa, ertaga uchun rejalashtiriladi
            target += timedelta(days=1)

        sleep_seconds = (target - now).total_seconds()
        logger.info(f"Scheduler will run next at {target} (sleeping for {sleep_seconds:.1f} seconds)")
        await asyncio.sleep(sleep_seconds)

        try:
            await send_tomorrow_notifications(bot)
        except Exception as e:
            logger.error(f"Error in send_tomorrow_notifications: {e}")

        # Bir xil daqiqada ikki marta ishga tushmaslik uchun
        await asyncio.sleep(60)
