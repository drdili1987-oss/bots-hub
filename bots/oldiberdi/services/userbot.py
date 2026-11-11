import logging
import os
import re
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    UserPrivacyRestrictedError,
    FloodWaitError,
)
from telethon.tl.functions.contacts import ImportContactsRequest, DeleteContactsRequest
from telethon.tl.types import InputPhoneContact
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_SESSION_STRING

logger = logging.getLogger(__name__)

SESSION_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "userbot")


class UserBotService:
    def __init__(self):
        self.api_id = TELEGRAM_API_ID or os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = TELEGRAM_API_HASH or os.getenv("TELEGRAM_API_HASH", "")
        self.session_string = TELEGRAM_SESSION_STRING or os.getenv("TELEGRAM_SESSION_STRING", "")
        self.client: Optional[TelegramClient] = None
        self._is_ready = False

    def is_configured(self) -> bool:
        self.api_id = TELEGRAM_API_ID or os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = TELEGRAM_API_HASH or os.getenv("TELEGRAM_API_HASH", "")
        self.session_string = TELEGRAM_SESSION_STRING or os.getenv("TELEGRAM_SESSION_STRING", "")
        session_file = f"{SESSION_PATH}.session"
        return bool(self.api_id and self.api_hash and (self.session_string or os.path.exists(session_file)))

    def is_active(self) -> bool:
        return bool(self.client and self.client.is_connected() and self._is_ready)

    async def start(self) -> bool:
        if not self.is_configured():
            logger.info("Userbot sozlanmagan (TELEGRAM_SESSION_STRING yoki userbot.session hali mavjud emas).")
            return False

        try:
            if self.session_string:
                session = StringSession(self.session_string.strip())
            else:
                session = SESSION_PATH
            self.client = TelegramClient(session, int(self.api_id), self.api_hash)
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.warning("Userbot avtorizatsiyadan o'tmagan. login_userbot.py orqali kiring.")
                await self.client.disconnect()
                self._is_ready = False
                return False
            me = await self.client.get_me()
            self._is_ready = True
            logger.info("Userbot muvaffaqiyatli ulandi: %s (@%s)", me.first_name, me.username or "yo'q")
            return True
        except Exception as e:
            logger.error("Userbotni ishga tushirishda xatolik: %s", e)
            self._is_ready = False
            return False

    async def stop(self) -> None:
        if self.client and self.client.is_connected():
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self._is_ready = False

    async def send_pm(self, target: str, message: str) -> Tuple[bool, str, Optional[int]]:
        """
        target: '@username' yoki '+998901234567' yoki '901234567' yoki '8406822179' (user_id)
        Returns: (success, status_text, telegram_user_id)
        """
        if not self.is_active():
            return False, "Userbot faol emas", None

        target = str(target).strip()

        # 1. Agar Telegram User ID bo'lsa (faqat raqamlar va uzunligi 10 dan ortiq bo'lsa yoki 998 bilan boshlanmasa)
        if target.isdigit() and len(target) < 12 and not (len(target) == 9 and target[:2] in ("90", "91", "93", "94", "95", "97", "98", "99", "88", "33", "77", "50", "20", "29", "71", "78")):
            try:
                entity = await self.client.get_entity(int(target))
                await self.client.send_message(entity, message, parse_mode="html")
                return True, "Shaxsiyiga xabar yuborildi", getattr(entity, "id", int(target))
            except UserPrivacyRestrictedError:
                return False, "Foydalanuvchi maxfiylik sozlamalari tufayli xabar qabul qilmaydi", int(target)
            except Exception as e:
                logger.warning("Userbot user_id orqali topa olmadi (%s): %s", target, e)

        # 2. Agar @username bo'lsa
        if target.startswith("@") or (not any(c.isdigit() for c in target) and not target.startswith("+")):
            try:
                entity = await self.client.get_entity(target)
                await self.client.send_message(entity, message, parse_mode="html")
                return True, "Shaxsiyiga xabar yuborildi", getattr(entity, "id", None)
            except UserPrivacyRestrictedError:
                return False, "Foydalanuvchi maxfiylik sozlamalari tufayli xabar qabul qilmaydi", None
            except Exception as e:
                logger.warning("Userbot username orqali topa olmadi (%s): %s", target, e)
                return False, str(e), None

        # 3. Agar telefon raqam bo'lsa
        digits = re.sub(r"\D", "", target)
        if len(digits) == 9:
            digits = "998" + digits
        clean_phone = digits

        try:
            try:
                # Avval raqam bo'yicha topishga urinamiz
                user = await self.client.get_entity(clean_phone)
            except Exception:
                # Agar topilmasa, kontaktga saqlab yozamiz
                contact = InputPhoneContact(client_id=0, phone=clean_phone, first_name="Kontakt", last_name="")
                res = await self.client(ImportContactsRequest([contact]))
                if not res.users:
                    return False, "Bu telefon raqam Telegramda ro'yxatdan o'tmagan", None
                user = res.users[0]

            try:
                await self.client.send_message(user, message, parse_mode="html")
            except UserPrivacyRestrictedError:
                return False, "Foydalanuvchi shaxsiyiga yozish taqiqlangan (Privacy settings)", user.id

            return True, "Shaxsiyiga xabar yuborildi", user.id

        except FloodWaitError as e:
            logger.error("FloodWait: %s soniya kuting", e.seconds)
            return False, f"Telegram cheklovi: {e.seconds} soniya kuting", None
        except Exception as e:
            logger.error("Userbot orqali xabar yuborishda xatolik: %s", e)
            return False, str(e), None


userbot_service = UserBotService()
