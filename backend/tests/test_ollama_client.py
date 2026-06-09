import app.llm.ollama_client as oc
from app.schemas import Post


class FakeResp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._p


def _post():
    return Post(author="Acme", text="We're hiring an AI Engineer in NYC", permalink="p1")


def test_classify_valid_job(monkeypatch):
    def fake_post(url, **kwargs):
        return FakeResp(
            {
                "response": '{"is_job": true, "role_title": "AI Engineer", '
                '"company": "Acme", "location": "NYC", "seniority": "Mid", '
                '"relevance_score": 0.9, "one_line_summary": "Hiring AI Engineer"}'
            }
        )

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    cls = oc.classify_post(_post(), ["AI Engineer"], "gemma4:12b")
    assert cls.is_job is True
    assert cls.role_title == "AI Engineer"
    assert cls.relevance_score == 0.9


def test_classify_retry_then_valid(monkeypatch):
    calls = {"n": 0}

    def fake_post(url, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeResp({"response": "this is not json"})
        return FakeResp({"response": '{"is_job": false, "relevance_score": 0.1}'})

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    cls = oc.classify_post(_post(), ["AI Engineer"], "gemma4:12b")
    assert calls["n"] == 2
    assert cls.is_job is False


def test_classify_all_bad_fallback(monkeypatch):
    def fake_post(url, **kwargs):
        return FakeResp({"response": "garbage <<<"})

    monkeypatch.setattr(oc.httpx, "post", fake_post)
    cls = oc.classify_post(_post(), ["AI Engineer"], "gemma4:12b")
    assert cls.is_job is False
    assert cls.relevance_score == 0.0
