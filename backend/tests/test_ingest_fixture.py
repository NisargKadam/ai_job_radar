from app.agent.nodes.ingest import ingest


def test_ingest_fixture_mode():
    out = ingest({"settings": {"fixture_mode": True}, "errors": []})
    assert len(out["raw_posts"]) == 8
    assert all(p.source == "fixture" for p in out["raw_posts"])
    assert out["raw_posts"][0].permalink.startswith("https://www.linkedin.com/feed/update/")
