from fastapi.testclient import TestClient

from app.main import create_app


def test_health_shape():
    client = TestClient(create_app())
    with client:
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    for key in ("status", "ollama", "browser_session", "delivery"):
        assert key in body
    assert body["status"] == "ok"
    assert isinstance(body["ollama"], bool)


def test_settings_roundtrip():
    client = TestClient(create_app())
    with client:
        r = client.get("/settings")
        assert r.status_code == 200
        assert r.json()["min_posts"] == 5

        r2 = client.put("/settings", json={"min_posts": 7})
        assert r2.status_code == 200
        assert r2.json()["min_posts"] == 7
