"""WhatsApp delivery via the macOS WhatsApp desktop app (DEFERRED).

Intended approach (see docs/whatsapp-macos-notes.md): drive the native macOS
WhatsApp app with AppleScript/`osascript` UI scripting and/or the
`whatsapp://send?...` URL scheme — NOT whatsapp-web.js.

WARNING: unofficial, against WhatsApp's Terms of Service, risk of number ban.
Use a non-primary number. Group selection via UI scripting is brittle and must
be hardened before enabling.
"""
from app.delivery.base import DeliveryChannel, SendResult


class WhatsAppChannel(DeliveryChannel):
    name = "whatsapp"

    def send(self, group_id: str, message: str) -> SendResult:
        raise NotImplementedError(
            "WhatsApp delivery via the macOS app is deferred — not implemented yet. "
            "See docs/whatsapp-macos-notes.md."
        )

    def health(self) -> bool:
        return False
