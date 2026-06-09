import json
import pathlib

import app.agent.nodes.classify as cl
from app.agent.nodes.classify import classify
from app.db.models import Seen
from app.db.session import SessionLocal, init_db
from app.schemas import Classification, Post

FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "sample_posts.json"


def _load_posts():
    data = json.loads(FIX.read_text())
    return [Post(source="fixture", **p) for p in data]


def _stub(post, keywords, model):
    is_job = any(
        kw in post.text.lower()
        for kw in ["hiring", "open role", "we're looking", "join our team"]
    )
    return Classification(is_job=is_job, relevance_score=0.8 if is_job else 0.1)


def test_classify_processes_all_unseen(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/c.db")
    init_db()
    monkeypatch.setattr(cl, "classify_post", _stub)

    posts = _load_posts()
    state = {"raw_posts": posts, "settings": {"keywords": ["AI Engineer"], "ollama_model": "x"}, "errors": []}
    out = classify(state)
    assert len(out["classified"]) == 8


def test_classify_skips_seen_permalinks(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/c2.db")
    init_db()
    monkeypatch.setattr(cl, "classify_post", _stub)

    posts = _load_posts()
    # mark the first 3 as already seen (review_gate writes Seen in real runs)
    with SessionLocal() as s:
        for p in posts[:3]:
            s.add(Seen(permalink=p.permalink))
        s.commit()

    out = classify({"raw_posts": posts, "settings": {"keywords": ["x"], "ollama_model": "x"}, "errors": []})
    assert len(out["classified"]) == 5
