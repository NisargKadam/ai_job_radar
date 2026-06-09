from fastapi import APIRouter

from app.schemas import SettingsIn, SettingsOut
from app.settings_service import get_settings, update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def read_settings() -> SettingsOut:
    return get_settings()


@router.put("", response_model=SettingsOut)
def write_settings(patch: SettingsIn) -> SettingsOut:
    saved = update_settings(patch)
    if patch.schedule_time is not None:
        from app.scheduler import reschedule

        reschedule(saved.schedule_time)
    return saved
