import os

import httpx
from fastapi import APIRouter

from app.config import config
from app.schemas import HealthOut
from app.settings_service import get_settings

router = APIRouter()


def ollama_reachable() -> bool:
    try:
        r = httpx.get(f"{config.ollama_base_url}/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def browser_session_valid() -> bool:
    """Heuristic: the persistent user-data-dir exists and is non-empty,
    meaning a manual LinkedIn login has been performed at least once."""
    d = config.aijr_user_data_dir
    return os.path.isdir(d) and any(os.scandir(d))


def delivery_configured() -> bool:
    s = get_settings()
    if s.delivery_channel == "telegram":
        return bool(config.telegram_bot_token) and len(s.group_ids) > 0
    return False  # whatsapp deferred


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(
        status="ok",
        ollama=ollama_reachable(),
        browser_session=browser_session_valid(),
        delivery=delivery_configured(),
    )
