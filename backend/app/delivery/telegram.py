import httpx

from app.config import config
from app.delivery.base import DeliveryChannel, SendResult

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramChannel(DeliveryChannel):
    name = "telegram"

    def __init__(self, token: str | None = None):
        self.token = token if token is not None else config.telegram_bot_token

    def send(self, group_id: str, message: str) -> SendResult:
        if not self.token:
            return SendResult(ok=False, error="missing TELEGRAM_BOT_TOKEN")
        try:
            r = httpx.post(
                API.format(token=self.token, method="sendMessage"),
                json={
                    "chat_id": group_id,
                    "text": message,
                    "disable_web_page_preview": False,
                },
                timeout=20,
            )
            if r.status_code == 200 and r.json().get("ok"):
                return SendResult(ok=True)
            return SendResult(ok=False, error=f"telegram {r.status_code}: {r.text[:200]}")
        except Exception as e:
            return SendResult(ok=False, error=str(e))

    def health(self) -> bool:
        if not self.token:
            return False
        try:
            r = httpx.get(API.format(token=self.token, method="getMe"), timeout=10)
            return r.status_code == 200 and bool(r.json().get("ok"))
        except Exception:
            return False
