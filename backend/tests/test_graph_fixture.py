import app.agent.nodes.classify as cl
from app.agent.graph import run_pipeline
from app.db.models import Candidate, Run
from app.db.session import SessionLocal, init_db
from app.schemas import Classification
from app.settings_service import update_settings
from app.schemas import SettingsIn

_TRIGGERS = ["hiring", "open role", "opening", "looking for", "apply"]


def _stub(post, keywords, model):
    is_job = any(t in post.text.lower() for t in _TRIGGERS)
    return Classification(
        is_job=is_job,
        relevance_score=0.9 if is_job else 0.1,
        role_title="AI Engineer" if is_job else None,
        company="Acme" if is_job else None,
    )


def test_pipeline_fixture_fills_review_queue(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/g.db")
    init_db()
    update_settings(SettingsIn(fixture_mode=True, dry_run=True, auto_send=False))
    monkeypatch.setattr(cl, "classify_post", _stub)

    with SessionLocal() as s:
        run = Run(status="running")
        s.add(run)
        s.commit()
        rid = run.id

    run_pipeline(rid)

    with SessionLocal() as s:
        r = s.get(Run, rid)
        assert r.status == "finished"
        assert r.posts_seen == 8
        pending = s.query(Candidate).filter_by(status="pending").count()
    assert r.jobs_found >= 5
    assert pending >= 5


def test_pipeline_dedup_across_runs(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/g2.db")
    init_db()
    update_settings(SettingsIn(fixture_mode=True, dry_run=True, auto_send=False))
    monkeypatch.setattr(cl, "classify_post", _stub)

    for _ in range(2):
        with SessionLocal() as s:
            run = Run(status="running")
            s.add(run)
            s.commit()
            rid = run.id
        run_pipeline(rid)

    with SessionLocal() as s:
        # second run should add no new candidates (all permalinks already seen)
        total = s.query(Candidate).count()
    assert total >= 5
    # exactly the unique job count, not doubled
    assert total <= 8
