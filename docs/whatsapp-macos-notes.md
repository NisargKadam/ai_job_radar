# WhatsApp delivery via the macOS app (deferred)

> **Status:** not implemented. `WhatsAppChannel.send` currently raises `NotImplementedError`.
> Telegram is the supported channel. This note records the intended approach so it
> can be built later without re-deciding the design.

## Why the macOS app (not whatsapp-web.js)

Per the project owner's constraint, WhatsApp delivery must go through the **native
WhatsApp desktop app on macOS** — not the `whatsapp-web.js` Node library. So the
channel drives the installed app via macOS automation rather than running a separate
web session.

## ⚠️ Terms-of-Service warning

Automating WhatsApp in any unofficial way is **against WhatsApp's Terms of Service and
risks a number ban**. Use a **non-primary number**, keep volume low, and treat this as
experimental. This is surfaced in the Settings UI when the WhatsApp channel is selected.

## Intended implementation

`backend/app/delivery/whatsapp_macos.py` → `WhatsAppChannel.send(group_id, message)`:

1. **URL scheme (preferred, least brittle):** open
   `whatsapp://send?text=<urlencoded message>` via `open` / `osascript`. This focuses
   the app with the message pre-filled, but **does not pick a recipient** — group
   selection still needs a UI step.
2. **AppleScript UI scripting (for group targeting):** use `osascript` with System
   Events to (a) focus WhatsApp, (b) search/select the target chat by name, (c) paste
   the message, (d) press Return. Example skeleton:

   ```applescript
   tell application "WhatsApp" to activate
   tell application "System Events" to tell process "WhatsApp"
       keystroke "f" using command down      -- focus search
       keystroke "<group name>"
       delay 0.6
       key code 36                            -- Return: open top result
       delay 0.4
       keystroke "<message>"
       key code 36                            -- Return: send
   end tell
   ```

   Called from Python via `subprocess.run(["osascript", "-e", script], ...)`.

## Known challenges (harden before enabling)

- **`group_id` is a chat *name*, not a numeric id** here — UI scripting selects by the
  visible chat title, so the Settings `group_ids` for WhatsApp must be exact chat names.
- **Accessibility permission:** the controlling process (Terminal / the Python binary)
  needs *System Settings → Privacy & Security → Accessibility* enabled, or System
  Events keystrokes silently fail.
- **Timing/races:** `delay`s are fragile; search results can shift. Needs retries and
  verification that the right chat opened before sending.
- **Multi-line messages:** newlines can trigger send early; may need to paste via the
  clipboard (`pbcopy` + Cmd-V) instead of `keystroke`.

## How it plugs in

The `DeliveryChannel` interface and `get_channel(settings)` factory already route
`delivery_channel == "whatsapp"` to `WhatsAppChannel`. Implementing `send()` (and
`health()` to check the app is installed/running) is all that's required — no pipeline
or API changes.
