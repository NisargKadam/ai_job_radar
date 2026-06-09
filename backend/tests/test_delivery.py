from datetime import datetime, timezone

import app.delivery.telegram as tg
from app.delivery.formatting import format_digest, format_individual
from app.delivery.telegram import TelegramChannel
from app.schemas import CandidateOut


def _cand(i: int) -> CandidateOut:
    return CandidateOut(
        id=i,
        run_id=1,
        permalink=f"https://lnkd.in/{i}",
        author="Acme",
        role_title="AI Engineer",
        company="Acme",
        location="NYC",
        seniority="Mid",
        relevance_score=0.9,
        summary="Great role",
        raw_text="...",
        status="approved",
        created_at=datetime.now(timezone.utc),
    )


def test_format_digest_lists_all():
    msg = format_digest([_cand(1), _cand(2)])
    assert "2 AI/ML job opportunities" in msg
    assert "AI Engineer" in msg
    assert "https://lnkd.in/1" in msg
    assert "https://lnkd.in/2" in msg


def test_format_individual():
    msg = format_individual(_cand(1))
    assert "AI Engineer" in msg
    assert "https://lnkd.in/1" in msg


class FakeResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._p = payload
        self.text = str(payload)

    def json(self):
        return self._p


def test_telegram_send_ok(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs.get("json")
        return FakeResp(200, {"ok": True, "result": {}})

    monkeypatch.setattr(tg.httpx, "post", fake_post)
    res = TelegramChannel(token="T").send("-100123", "hello")
    assert res.ok is True
    assert "/botT/sendMessage" in captured["url"]
    assert captured["json"]["chat_id"] == "-100123"
    assert captured["json"]["text"] == "hello"


def test_telegram_send_error(monkeypatch):
    def fake_post(url, **kwargs):
        return FakeResp(400, {"ok": False, "description": "chat not found"})

    monkeypatch.setattr(tg.httpx, "post", fake_post)
    res = TelegramChannel(token="T").send("-100", "hi")
    assert res.ok is False
    assert "400" in res.error


def test_telegram_missing_token():
    res = TelegramChannel(token="").send("-100", "hi")
    assert res.ok is False
    assert "TELEGRAM_BOT_TOKEN" in res.error
