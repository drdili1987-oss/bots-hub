import logging
import re
from typing import Optional, Tuple
import aiohttp
from config import (
    ESKIZ_EMAIL,
    ESKIZ_PASSWORD,
    ESKIZ_FROM,
    SMS_GATEWAY_URL,
    SMS_GATEWAY_LOGIN,
    SMS_GATEWAY_PASSWORD,
)

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if len(digits) == 9:
        digits = "998" + digits
    return digits


class AndroidSMSGateway:
    """Android SMS Gateway (masalan: sms-gate.app yoki local Android HTTP server)."""

    def __init__(self, url: str = "", login: str = "", password: str = ""):
        self.url = (url or "").strip()
        self.login = (login or "").strip()
        self.password = (password or "").strip()

    async def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        if not self.url:
            return False, "SMS Gateway URL sozlanmagan"

        clean_phone = normalize_phone(phone)
        endpoint = self.url
        if not (endpoint.endswith("/message") or endpoint.endswith("/send")):
            endpoint = endpoint.rstrip("/") + "/message"

        payload = {
            "phoneNumbers": [f"+{clean_phone}"],
            "message": message,
        }

        auth = None
        if self.login or self.password:
            auth = aiohttp.BasicAuth(self.login, self.password)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    auth=auth,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status in (200, 201, 202):
                        logger.info("Android SMS Gateway orqali SMS yuborildi: +%s", clean_phone)
                        return True, "Android telefon orqali SMS yuborildi"
                    text = await resp.text()
                    logger.warning("Android SMS Gateway xatolik (%s): %s", resp.status, text)
                    return False, f"Gateway xatosi: HTTP {resp.status}"
        except Exception as e:
            logger.error("Android SMS Gateway ulanish xatosi: %s", e)
            return False, f"Telefonga ulanib bo'lmadi ({e})"


class EskizSMS:
    BASE_URL = "https://notify.eskiz.uz/api"

    def __init__(self, email: str = "", password: str = "", from_sender: str = "4546"):
        self.email = email
        self.password = password
        self.from_sender = from_sender or "4546"
        self._token: Optional[str] = None

    async def _get_token(self, session: aiohttp.ClientSession) -> Optional[str]:
        if self._token:
            return self._token
        if not self.email or not self.password:
            return None
        try:
            async with session.post(
                f"{self.BASE_URL}/auth/login",
                data={"email": self.email, "password": self.password},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and isinstance(data, dict):
                    token = data.get("data", {}).get("token")
                    if token:
                        self._token = token
                        return self._token
                logger.error("Eskiz login muvaffaqiyatsiz: %s", data)
                return None
        except Exception as e:
            logger.error("Eskiz login exception: %s", e)
            return None

    async def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        if not self.email or not self.password:
            return False, "Eskiz hisobi sozlanmagan"

        clean_phone = normalize_phone(phone)
        if not (clean_phone.startswith("998") and len(clean_phone) == 12):
            return False, f"Noto'g'ri telefon raqam formati: {phone}"

        async with aiohttp.ClientSession() as session:
            token = await self._get_token(session)
            if not token:
                return False, "Eskiz tizimiga kirib bo'lmadi (login/parol xato)"

            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "mobile_phone": clean_phone,
                "message": message,
                "from": self.from_sender,
            }

            try:
                async with session.post(
                    f"{self.BASE_URL}/message/sms/send",
                    data=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    resp_data = await resp.json()
                    if resp.status == 200:
                        logger.info("SMS muvaffaqiyatli yuborildi: %s", clean_phone)
                        return True, "Muvaffaqiyatli yuborildi"
                    return False, str(resp_data.get("message", resp_data))
            except Exception as e:
                logger.error("SMS yuborishda xatolik: %s", e)
                return False, str(e)


class UnifiedSMSService:
    """Agar Android SMS Gateway sozlangan bo'lsa - undan jo'natadi, aks holda Eskiz'dan."""

    def __init__(self):
        self.android = AndroidSMSGateway(
            url=SMS_GATEWAY_URL,
            login=SMS_GATEWAY_LOGIN,
            password=SMS_GATEWAY_PASSWORD,
        )
        self.eskiz = EskizSMS(
            email=ESKIZ_EMAIL,
            password=ESKIZ_PASSWORD,
            from_sender=ESKIZ_FROM,
        )

    def normalize_phone(self, phone: str) -> str:
        return normalize_phone(phone)

    async def send_sms(self, phone: str, message: str) -> Tuple[bool, str]:
        errors = []
        # 1. Android SMS Gateway
        if self.android.url:
            ok, msg = await self.android.send_sms(phone, message)
            if ok:
                return True, msg
            logger.warning("Android SMS Gateway orqali jo'natilmadi (%s), boshqa usul tekshirilmoqda...", msg)
            errors.append(f"Android Gateway: {msg}")

        # 2. Eskiz
        if self.eskiz.email and self.eskiz.password:
            ok, msg = await self.eskiz.send_sms(phone, message)
            if ok:
                return True, msg
            logger.warning("Eskiz SMS yuborishda xatolik: %s", msg)
            errors.append(f"Eskiz: {msg}")

        reason = "; ".join(errors) if errors else "SMS shlyuz sozlanmagan"
        return False, reason



sms_service = UnifiedSMSService()
