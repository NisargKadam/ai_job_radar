import time

from fastapi.testclient import TestClient

import app.agent.nodes.classify as cl
from app.schemas import Classification

_TRIGGERS = ["hiring", "open role", "opening", "looking for", "apply"]


def _stub(post, keywords, model):
    is_job = any(t in post.text.lower() for t in _TRIGGERS)
    return Classification(
        is_job=is_job,
        relevance_score=0.9 if is_job else 0.1,
        role_title="AI Engineer" if is_job else None,
        company="Acme" if is_job else None,
        location="NYC" if is_job else None,
    )


def test_run_endpoint_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/api.db")
    monkeypatch.setattr(cl, "classify_post", _stub)

    from app.main import create_app

    client = TestClient(create_app())
    with client:
        client.put(
            "/settings",
            json={
                "fixture_mode": True,
                "dry_run": True,
                "auto_send": False,
                "group_ids": ["-100123"],
            },
        )
        r = client.post("/run")
        assert r.status_code == 200
        rid = r.json()["run_id"]

        detail = None
        for _ in range(100):
            detail = client.get(f"/runs/{rid}").json()
            if detail["status"] in ("finished", "error"):
                break
            time.sleep(0.1)
        assert detail["status"] == "finished", detail
        assert detail["posts_seen"] == 8

        pending = client.get("/candidates", params={"status": "pending"}).json()
        assert len(pending) >= 5

        # approve / reject toggles
        assert client.post(f"/candidates/{pending[0]['id']}/approve").json()["status"] == "approved"
        assert client.post(f"/candidates/{pending[1]['id']}/reject").json()["status"] == "rejected"

        # send (dry-run) of approved
        send = client.post("/send").json()
        assert send["dry_run"] is True
        assert send["sent"] == 0
        assert any("dry-run" in d for d in send["details"])
