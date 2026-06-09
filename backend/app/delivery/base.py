from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SendResult:
    ok: bool
    error: str | None = None


class DeliveryChannel(ABC):
    name = "base"

    @abstractmethod
    def send(self, group_id: str, message: str) -> SendResult:
        ...

    @abstractmethod
    def health(self) -> bool:
        ...


def get_channel(settings: dict) -> DeliveryChannel:
    ch = settings.get("delivery_channel", "telegram")
    if ch == "telegram":
        from app.delivery.telegram import TelegramChannel

        return TelegramChannel()
    if ch == "whatsapp":
        from app.delivery.whatsapp_macos import WhatsAppChannel

        return WhatsAppChannel()
    raise ValueError(f"unknown delivery channel: {ch}")
