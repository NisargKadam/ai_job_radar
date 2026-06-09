import pytest

from app.db.models import Candidate, SettingsRow
from app.db.session import SessionLocal, init_db


def test_init_db_creates_singleton_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/t.db")
    init_db()
    with SessionLocal() as s:
        rows = s.query(SettingsRow).all()
        assert len(rows) == 1
        assert rows[0].min_posts == 5
        assert rows[0].dry_run is True
        assert "AI Engineer" in rows[0].keywords


def test_candidate_permalink_unique(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/t2.db")
    init_db()
    with SessionLocal() as s:
        s.add(Candidate(permalink="x", status="pending"))
        s.commit()
    with SessionLocal() as s:
        s.add(Candidate(permalink="x", status="pending"))
        with pytest.raises(Exception):
            s.commit()
