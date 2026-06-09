from app.db.session import init_db
from app.schemas import SettingsIn, SettingsOut
from app.settings_service import get_settings, update_settings


def test_get_and_update_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/s.db")
    init_db()

    s = get_settings()
    assert isinstance(s, SettingsOut)
    assert s.min_posts == 5

    updated = update_settings(SettingsIn(min_posts=8, group_ids=["-100123", "-100456"]))
    assert updated.min_posts == 8
    assert updated.group_ids == ["-100123", "-100456"]
    # persisted
    assert get_settings().min_posts == 8
