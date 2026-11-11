import logging
from datetime import datetime, timezone, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import database as db
from config import ADMIN_IDS, REMINDER_INTERVAL_DAYS
from services.userbot import userbot_service
from services.sms import sms_service

logger = logging.getLogger(__name__)

# O'zbekiston vaqti (Tashkent: UTC+5)
UZ_TZ = timezone(timedelta(hours=5))
OVERDUE_FOOTER = "\n\n⚠️ <i>Qarz munosabatni buzadi.</i>"


async def _send_notification_to_user(bot: Bot, user_id: str, phone: str, text: str) -> bool:
    """Xabarni bot, userbot yoki SMS orqali foydalanuvchiga yuboradi."""
    sent = False
    if user_id and str(user_id).isdigit():
        try:
            await bot.send_message(int(user_id), text)
            sent = True
        except Exception as exc:
            logger.debug("Bot notification failed for %s: %s", user_id, exc)

    if not sent and userbot_service.is_active():
        target = str(user_id) if user_id else phone
        if target:
            ok, _, _ = await userbot_service.send_pm(target, text)
            sent = ok

    if not sent and phone:
        plain_text = text.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", "")
        ok_sms, _ = await sms_service.send_sms(phone, plain_text)
        sent = ok_sms

    return sent


async def _check_and_notify(bot: Bot, is_evening: bool = False) -> None:
    debts = db.get_all_debts()
    now_uz = datetime.now(UZ_TZ)
    today_date = now_uz.date()
    slot_name = "evening" if is_evening else "morning"
    current_slot = f"{today_date}_{slot_name}"

    for debt_id, debt in debts.items():
        if debt.get("status") != "active":
            continue

        last_slot = debt.get("last_notified_slot")
        if last_slot == current_slot:
            continue

        debtor_id = debt.get("debtor_id")
        creditor_id = debt.get("creditor_id")
        phone = debt.get("phone", "")
        amount = debt.get("amount", 0)
        currency = debt.get("currency", "UZS")
        due_date_str = debt.get("due_date")
        amount_fmt = db.format_amount(amount)

        # Ismlarni olish
        debtor_user = db.get_user(debtor_id) if debtor_id else None
        debtor_name = debtor_user.get("full_name", "Qarzdor") if debtor_user else (debt.get("creator_alias") or "Qarzdor")

        creditor_user = db.get_user(creditor_id) if creditor_id else None
        creditor_name = creditor_user.get("full_name", "Haqdor") if creditor_user else "Haqdor"

        debtor_msg = ""
        creditor_msg = ""
        should_send = False

        if due_date_str:
            try:
                clean_due = due_date_str.replace("/", ".").replace("-", ".")
                parts = clean_due.split(".")
                if len(parts) == 3 and len(parts[0]) == 4:
                    due_date_obj = datetime.strptime(clean_due, "%Y.%m.%d").date()
                else:
                    due_date_obj = datetime.strptime(clean_due, "%d.%m.%Y").date()
                
                days_left = (due_date_obj - today_date).days

                if not is_evening:
                    if days_left == 1:
                        # 1 kun oldin xabarnoma (Ertaga pul berish/olish kuni)
                        should_send = True
                        debtor_msg = (
                            f"⏰ <b>Qarz eslatmasi (1 kun qoldi)!</b>\n\n"
                            f"Ertaga <b>{creditor_name}</b>ga <b>{amount_fmt} {currency}</b> qarzni qaytarish kuni."
                        )
                        creditor_msg = (
                            f"⏰ <b>Qarz eslatmasi (1 kun qoldi)!</b>\n\n"
                            f"Ertaga <b>{debtor_name}</b> sizga <b>{amount_fmt} {currency}</b> qarzni qaytarishi kerak."
                        )
                    elif days_left == 0:
                        # Belgilangan muddat kuni ertalab xabarnoma
                        should_send = True
                        debtor_msg = (
                            f"🔔 <b>Bugun qarzni qaytarish kuni!</b>\n\n"
                            f"Bugun <b>{creditor_name}</b>ga <b>{amount_fmt} {currency}</b> qarzni qaytarishingiz kerak."
                        )
                        creditor_msg = (
                            f"🔔 <b>Bugun qarzni qaytarish kuni!</b>\n\n"
                            f"Bugun <b>{debtor_name}</b> sizga <b>{amount_fmt} {currency}</b> qarzni qaytarishi kerak."
                        )
                    elif days_left < 0:
                        # Muddati o'tgan qarzlar (Ertasidan boshlab har kuni 8:00 va 20:00)
                        should_send = True
                        debtor_msg = (
                            f"🚨 <b>Qarz muddati o'tib ketgan!</b>\n\n"
                            f"<b>{creditor_name}</b> oldidagi <b>{amount_fmt} {currency}</b> miqdoridagi qarzingiz muddati o'tib ketgan. Iltimos, qarzni tezroq qaytaring!"
                            f"{OVERDUE_FOOTER}"
                        )
                        creditor_msg = (
                            f"🚨 <b>Qarz muddati o'tib ketgan!</b>\n\n"
                            f"<b>{debtor_name}</b> ning <b>{amount_fmt} {currency}</b> miqdoridagi qarzi muddati o'tib ketgan."
                            f"{OVERDUE_FOOTER}"
                        )
                else:
                    # Kechki seans (20:00) - faqat muddati o'tgan qarzlar uchun
                    if days_left < 0:
                        should_send = True
                        debtor_msg = (
                            f"🚨 <b>Qarz muddati o'tib ketgan!</b>\n\n"
                            f"<b>{creditor_name}</b> oldidagi <b>{amount_fmt} {currency}</b> miqdoridagi qarzingiz muddati o'tib ketgan. Iltimos, qarzni tezroq qaytaring!"
                            f"{OVERDUE_FOOTER}"
                        )
                        creditor_msg = (
                            f"🚨 <b>Qarz muddati o'tib ketgan!</b>\n\n"
                            f"<b>{debtor_name}</b> ning <b>{amount_fmt} {currency}</b> miqdoridagi qarzi muddati o'tib ketgan."
                            f"{OVERDUE_FOOTER}"
                        )
            except Exception as e:
                logger.warning("Sana tahlil qilishda xatolik (debt_id=%s): %s", debt_id, e)
        else:
            # Muddat ko'rsatilmagan qarzlar uchun (faqat ertalab 8:00 da, davriy eslatma)
            if not is_evening:
                last_notified = debt.get("last_notified_at")
                last_dt = None
                if isinstance(last_notified, str):
                    try:
                        last_dt = datetime.fromisoformat(last_notified).date()
                    except ValueError:
                        pass
                
                days_passed = (today_date - last_dt).days if last_dt else REMINDER_INTERVAL_DAYS
                if days_passed >= REMINDER_INTERVAL_DAYS:
                    should_send = True
                    debtor_msg = (
                        f"🔔 <b>Qarz eslatmasi!</b>\n\n"
                        f"<b>{creditor_name}</b> bilan bo'lgan <b>{amount_fmt} {currency}</b> miqdoridagi qarz eslatilmoqda."
                    )
                    creditor_msg = (
                        f"🔔 <b>Qarz eslatmasi!</b>\n\n"
                        f"<b>{debtor_name}</b> bilan bo'lgan <b>{amount_fmt} {currency}</b> miqdoridagi qarz eslatilmoqda."
                    )

        if not should_send:
            continue

        # Har ikkala tomonga ham yuboramiz
        s1 = await _send_notification_to_user(bot, debtor_id, phone, debtor_msg)
        s2 = await _send_notification_to_user(bot, creditor_id, "", creditor_msg)

        if s1 or s2:
            db.update_debt_notified_slot(debt_id, current_slot)


async def _send_daily_admin_report(bot: Bot) -> None:
    if not ADMIN_IDS:
        return
    try:
        stats = db.get_stats()
        text = (
            "☀️ <b>Kunlik bot hisoboti (Temir Daftar):</b>\n\n"
            f"👥 Jami foydalanuvchilar: <b>{stats['total_users']} ta</b>\n"
            f"💳 Faol qarzlar soni: <b>{stats['active_debts_count']} ta</b>\n"
            f"💰 Faol qarzlar (UZS): <b>{db.format_amount(stats['total_uzs'])} UZS</b>\n"
            f"💵 Faol qarzlar (USD): <b>{db.format_amount(stats['total_usd'])} USD</b>\n\n"
            "Batafsil boshqaruv: /stats | /users | /find"
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(int(admin_id), text)
            except Exception as e:
                logger.warning("Kunlik hisobot yuborilmadi (admin=%s): %s", admin_id, e)
    except Exception as exc:
        logger.error("Admin hisobotini tayyorlashda xatolik: %s", exc)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=UZ_TZ)

    # 1-mahal: Har kuni ertalab 08:00 (Toshkent vaqti)
    scheduler.add_job(
        _check_and_notify,
        trigger=CronTrigger(hour=8, minute=0, timezone=UZ_TZ),
        args=(bot, False),
        id="debt_reminder_morning_job",
        replace_existing=True,
    )

    # 2-mahal: Har kuni kechki 20:00 (Toshkent vaqti) - faqat muddati o'tgan qarzlar uchun
    scheduler.add_job(
        _check_and_notify,
        trigger=CronTrigger(hour=20, minute=0, timezone=UZ_TZ),
        args=(bot, True),
        id="debt_reminder_evening_job",
        replace_existing=True,
    )

    # Har kuni ertalab soat 09:00 da adminga kunlik hisobot
    scheduler.add_job(
        _send_daily_admin_report,
        trigger=CronTrigger(hour=9, minute=0, timezone=UZ_TZ),
        args=(bot,),
        id="daily_admin_report_job",
        replace_existing=True,
    )

    return scheduler
