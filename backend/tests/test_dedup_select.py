from app.agent.nodes.dedup import dedup
from app.agent.nodes.select import select
from app.db.models import Candidate
from app.db.session import SessionLocal, init_db
from app.schemas import Classification, Post


def _c(permalink, is_job, score):
    return {
        "post": Post(permalink=permalink, text="t", author="a"),
        "cls": Classification(is_job=is_job, relevance_score=score),
    }


def test_dedup_drops_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/d.db")
    init_db()
    with SessionLocal() as s:
        s.add(Candidate(permalink="p1", status="pending"))
        s.commit()
    out = dedup({"classified": [_c("p1", True, 0.9), _c("p2", True, 0.8)]})
    perms = [c["post"].permalink for c in out["deduped"]]
    assert "p1" not in perms
    assert "p2" in perms


def test_select_filters_sorts_and_low_yield():
    deduped = [_c("a", True, 0.5), _c("b", False, 0.99), _c("c", True, 0.95)]
    out = select({"deduped": deduped, "settings": {"min_posts": 5}, "errors": []})
    sel = out["selected"]
    assert [c["post"].permalink for c in sel] == ["c", "a"]  # jobs only, desc by score
    assert any("low_yield" in e for e in out["errors"])


def test_select_no_low_yield_when_enough():
    deduped = [_c(str(i), True, 0.5) for i in range(6)]
    out = select({"deduped": deduped, "settings": {"min_posts": 5}, "errors": []})
    assert len(out["selected"]) == 6
    assert not any("low_yield" in e for e in out["errors"])
