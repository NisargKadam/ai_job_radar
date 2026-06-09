# AI Job Radar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A fully local, human-in-the-loop agentic app that scrapes LinkedIn (feed + keyword search) via a headful browser, classifies AI-job posts with a local Ollama model through an explicit LangGraph pipeline, lets the user approve candidates in a dark "operator console" UI, and pushes ≥5 jobs/day to 3 Telegram groups.

**Architecture:** Single FastAPI process hosts the REST API, APScheduler, the LangGraph pipeline, the Playwright headful browser (persistent user-data-dir), the Ollama client, and SQLite. Runs execute as background asyncio tasks. A React/Vite/Tailwind SPA polls the API. WhatsApp delivery (macOS app automation) is deferred to a stub.

**Tech Stack:** Python 3.13, FastAPI, Uvicorn, APScheduler, SQLAlchemy 2.x + SQLite, Pydantic v2, LangGraph, Playwright (Chromium headful), httpx (Ollama REST), pytest; React + Vite + TypeScript + Tailwind + Lucide.

**Reference spec:** `docs/superpowers/specs/2026-06-09-ai-job-radar-design.md`

---

## File Structure

```
backend/
  app/
    main.py                  FastAPI app factory, mounts routers, lifespan (db init, scheduler start)
    config.py                Settings from env (.env): db url, ollama url, telegram token, paths
    db/
      session.py             SQLAlchemy engine + SessionLocal + get_db dependency + init_db()
      models.py              Run, Candidate, Sent, SettingsRow, Seen, RunEvent ORM models
    schemas.py               Pydantic v2 models: Post, Classification, CandidateOut, SettingsIn/Out, RunOut, etc.
    settings_service.py      get_settings()/update_settings() against the singleton SettingsRow
    llm/ollama_client.py     classify_post() -> Classification via Ollama /api/generate format=json
    scraper/linkedin.py      LinkedInScraper: persistent context, login check, feed scroll, keyword search
    agent/
      state.py               AgentState TypedDict
      nodes/ingest.py        ingest node (browser OR fixture)
      nodes/classify.py      classify node (Ollama, seen-skip, retry)
      nodes/dedup.py         dedup node
      nodes/select.py        select node
      nodes/deliver.py       deliver node + deliver_approved() standalone path
      graph.py               build_graph() wiring + run_pipeline(run_id) background entrypoint
    delivery/
      base.py                DeliveryChannel ABC + SendResult + get_channel(settings)
      telegram.py            TelegramChannel
      whatsapp_macos.py      WhatsAppChannel stub (osascript, deferred)
      formatting.py          format_digest()/format_individual() message builders
    runner.py                RunManager: enqueue/track single active background run, log events
    scheduler.py             APScheduler daily job calling run_pipeline
    api/
      health.py              GET /health
      settings.py            GET/PUT /settings
      runs.py                POST /run, GET /runs, GET /runs/{id}
      candidates.py          GET /candidates, approve/reject/bulk
      send.py                POST /send
      linkedin.py            POST /linkedin/reauth
  fixtures/sample_posts.json Sample LinkedIn posts (mix of jobs + noise) for offline verification
  tests/                     pytest suite
  requirements.txt
  .env.example
frontend/                    Vite React TS + Tailwind (built via frontend-design skill)
README.md
```

---

## MILESTONE 1 — Backend scaffold + DB + settings + /health

### Task 1.1: Project deps + config

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py` (empty), `backend/app/config.py`

- [ ] **Step 1: requirements.txt**

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
sqlalchemy==2.0.*
pydantic==2.*
pydantic-settings==2.*
httpx==0.27.*
langgraph==0.2.*
playwright==1.48.*
apscheduler==3.10.*
python-dotenv==1.0.*
pytest==8.*
pytest-asyncio==0.24.*
```

- [ ] **Step 2: .env.example**

```
# Telegram (filled in at the delivery milestone)
TELEGRAM_BOT_TOKEN=
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
# Paths (defaults shown)
AIJR_DB_URL=sqlite:///./aijr.db
AIJR_USER_DATA_DIR=./.user-data
```

- [ ] **Step 3: config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")
    telegram_bot_token: str = ""
    ollama_base_url: str = "http://localhost:11434"
    aijr_db_url: str = "sqlite:///./aijr.db"
    aijr_user_data_dir: str = "./.user-data"

config = Config()
```

- [ ] **Step 4: Create venv + install + commit**

```bash
cd backend && python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
git add backend/requirements.txt backend/.env.example backend/app/config.py backend/app/__init__.py
git commit -m "chore: backend deps + config"
```

### Task 1.2: DB models + session

**Files:**
- Create: `backend/app/db/__init__.py`, `backend/app/db/session.py`, `backend/app/db/models.py`
- Test: `backend/tests/test_db.py`

- [ ] **Step 1: Write failing test** (`tests/test_db.py`)

```python
from app.db.session import init_db, SessionLocal
from app.db.models import SettingsRow, Candidate

def test_init_db_creates_singleton_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/t.db")
    init_db()
    with SessionLocal() as s:
        rows = s.query(SettingsRow).all()
        assert len(rows) == 1
        assert rows[0].min_posts == 5

def test_candidate_permalink_unique(tmp_path, monkeypatch):
    monkeypatch.setenv("AIJR_DB_URL", f"sqlite:///{tmp_path}/t2.db")
    init_db()
    with SessionLocal() as s:
        s.add(Candidate(permalink="x", status="pending")); s.commit()
        s.add(Candidate(permalink="x", status="pending"))
        import pytest
        with pytest.raises(Exception):
            s.commit()
```

- [ ] **Step 2: Run → fail** `./.venv/bin/pytest tests/test_db.py -v` → import error.

- [ ] **Step 3: session.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import config

class Base(DeclarativeBase): pass

engine = create_engine(config.aijr_db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

def init_db():
    from app.db import models  # noqa: F401
    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if s.query(models.SettingsRow).count() == 0:
            s.add(models.SettingsRow()); s.commit()

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
```

- [ ] **Step 4: models.py** — implement `Run, Candidate, Sent, SettingsRow, Seen, RunEvent` per spec §8. `SettingsRow` defaults: `keywords` (JSON list of the CONFIG keywords), `schedule_time="08:30"`, `min_posts=5`, `auto_send=False`, `dry_run=True`, `delivery_channel="telegram"`, `group_ids=[]` (JSON), `ollama_model="gemma4:12b"`, `fixture_mode=False`. Use `sqlalchemy.JSON` for list/dict columns, `DateTime` with server defaults.

- [ ] **Step 5: Run → pass** `./.venv/bin/pytest tests/test_db.py -v` → 2 passed.

- [ ] **Step 6: Commit** `git commit -am "feat: db models + session"`

### Task 1.3: settings_service + schemas

**Files:** Create `backend/app/schemas.py`, `backend/app/settings_service.py`; Test `backend/tests/test_settings.py`

- [ ] **Step 1: Failing test** — `update_settings({"min_posts": 8})` then `get_settings().min_posts == 8`; `get_settings()` returns a `SettingsOut` pydantic model.
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: schemas.py** — define `Post`, `Classification`, `SettingsIn` (all optional), `SettingsOut`, `CandidateOut`, `RunOut`, `RunEventOut`, `HealthOut`. `Classification`: `is_job: bool; role_title: str|None; company: str|None; location: str|None; seniority: str|None; relevance_score: float (ge=0,le=1); one_line_summary: str|None`.
- [ ] **Step 4: settings_service.py** — `get_settings()` reads singleton → `SettingsOut`; `update_settings(SettingsIn)` patches non-None fields, commits, returns `SettingsOut`.
- [ ] **Step 5: Run → pass. Step 6: Commit.**

### Task 1.4: FastAPI app + /health

**Files:** Create `backend/app/main.py`, `backend/app/api/__init__.py`, `backend/app/api/health.py`, `backend/app/api/settings.py`; Test `backend/tests/test_api_health.py`

- [ ] **Step 1: Failing test** — using `fastapi.testclient.TestClient`, `GET /health` → 200 and body has keys `ollama`, `browser_session`, `delivery`, `status`.
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: health.py** — `GET /health`: ping `{ollama_base_url}/api/tags` (httpx, short timeout) → `ollama: bool`; check persistent user-data-dir exists → `browser_session: bool`; check telegram token present + group_ids set → `delivery: bool`; `status: "ok"`.
- [ ] **Step 4: settings.py router** — `GET /settings`, `PUT /settings`.
- [ ] **Step 5: main.py** — `create_app()`: lifespan calls `init_db()`; mount CORS (allow `http://localhost:5173`); include routers.
- [ ] **Step 6: Run → pass. Commit.**

- [ ] **MILESTONE 1 VERIFY:** `./.venv/bin/uvicorn app.main:app --reload` then `curl localhost:8000/health` → JSON with `ollama:true` (Ollama is running). **Run this and confirm before continuing.**

---

## MILESTONE 2 — Ollama client + classify node (fixture-verified)

### Task 2.1: Ollama client

**Files:** Create `backend/app/llm/__init__.py`, `backend/app/llm/ollama_client.py`; Test `backend/tests/test_ollama_client.py`

- [ ] **Step 1: Failing test** — monkeypatch httpx to return a canned Ollama response whose `response` field is JSON for a job post; assert `classify_post(post, keywords, model)` returns a `Classification` with `is_job is True`. Second test: malformed JSON on first call, valid on retry → returns valid `Classification` (assert 2 calls). Third test: malformed both times → returns `Classification(is_job=False, relevance_score=0.0, ...)` fallback (never raises).
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: Implement**

```python
import json, httpx
from app.config import config
from app.schemas import Classification, Post

SYSTEM = (
    "You classify LinkedIn posts. Decide if a post is a GENUINE job opportunity "
    "for AI/ML/LLM/Agentic engineering roles. Consider these target keywords: {kw}. "
    "A 'job' means the author is hiring or sharing a specific open role (not generic "
    "advice, news, or self-promotion). Respond with ONLY a JSON object, no prose."
)
SCHEMA_HINT = (
    '{"is_job": bool, "role_title": string|null, "company": string|null, '
    '"location": string|null, "seniority": string|null, '
    '"relevance_score": number 0..1, "one_line_summary": string|null}'
)

def _prompt(post: Post, keywords: list[str], strict: bool) -> str:
    extra = "\nIMPORTANT: your previous reply was not valid JSON. Output ONLY the JSON object." if strict else ""
    return (
        SYSTEM.format(kw=", ".join(keywords))
        + f"\nReturn exactly this shape: {SCHEMA_HINT}{extra}\n\n"
        + f"POST AUTHOR: {post.author}\nPOST TEXT:\n{post.text}\n"
    )

def _call(prompt: str, model: str) -> str:
    r = httpx.post(
        f"{config.ollama_base_url}/api/generate",
        json={"model": model, "prompt": prompt, "format": "json", "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["response"]

def classify_post(post: Post, keywords: list[str], model: str) -> Classification:
    for strict in (False, True):
        try:
            raw = _call(_prompt(post, keywords, strict), model)
            return Classification.model_validate_json(raw)
        except Exception:
            continue
    return Classification(is_job=False, role_title=None, company=None, location=None,
                          seniority=None, relevance_score=0.0, one_line_summary=None)
```

- [ ] **Step 4: Run → pass. Commit.**

### Task 2.2: classify node + fixtures

**Files:** Create `backend/app/agent/__init__.py`, `backend/app/agent/state.py`, `backend/app/agent/nodes/__init__.py`, `backend/app/agent/nodes/classify.py`, `backend/fixtures/sample_posts.json`; Test `backend/tests/test_classify_node.py`

- [ ] **Step 1: state.py**

```python
from typing import TypedDict
from app.schemas import Post

class AgentState(TypedDict, total=False):
    run_id: int
    dry_run: bool
    auto_send: bool
    settings: dict
    raw_posts: list[Post]
    classified: list[dict]   # {"post": Post, "cls": Classification}
    deduped: list[dict]
    selected: list[dict]
    errors: list[str]
```

- [ ] **Step 2: sample_posts.json** — 8 posts: 5 genuine AI/ML/LLM hiring posts (varied roles/companies/locations), 3 noise (a conference recap, a "congrats on new role" post, a generic motivational post). Each: `{author, text, permalink, timestamp}`.
- [ ] **Step 3: Failing test** — build `AgentState` with `raw_posts` from fixture (loaded as `Post`), monkeypatch `classify_post` to a deterministic stub keyed by text; assert `classify(state)["classified"]` length == len(raw_posts) and that posts not in `seen` are classified. Test seen-skip: pre-seed `seen`, assert those are marked skipped/dropped.
- [ ] **Step 4: classify.py** — iterate `raw_posts`; skip (mark drop) permalinks already in `Seen`/`Sent`; else call `classify_post`; append `{"post","cls"}`; collect errors. Insert classified permalinks into `Seen`.
- [ ] **Step 5: Run → pass. Commit.**

- [ ] **MILESTONE 2 VERIFY (live Ollama):** small script `backend/scripts/try_classify.py` loads `fixtures/sample_posts.json`, calls real `classify_post` with `gemma4:12b`, prints each result. Run: `./.venv/bin/python scripts/try_classify.py` → confirm the 5 job posts get `is_job:true` and noise gets `is_job:false`, all valid JSON. **Confirm before continuing.**

---

## MILESTONE 3 — Playwright ingest + persistent context + re-auth + fixture mode

### Task 3.1: LinkedIn scraper

**Files:** Create `backend/app/scraper/__init__.py`, `backend/app/scraper/linkedin.py`

- [ ] **Step 1: Implement `LinkedInScraper`** (async Playwright). Methods:
  - `launch()` — `async_playwright().chromium.launch_persistent_context(user_data_dir, headless=False, viewport=...)`. NEVER headless.
  - `is_logged_in(page)` — navigate to `https://www.linkedin.com/feed/`; logged out if redirected to `/login` or `/authwall` or login form present.
  - `scrape_feed(max_scrolls)` — scroll with `random.uniform(2,6)` sleeps, hard cap on scrolls AND `MAX_SESSION_SECONDS`; extract posts via robust selectors (`div.feed-shared-update-v2`, author via `span.update-components-actor__name`, text via `.update-components-text`, permalink via `data-urn` → `…/feed/update/{urn}`). Graceful fallback selectors; skip posts missing text/permalink.
  - `search_posts(keyword, max_results)` — navigate to `https://www.linkedin.com/search/results/content/?keywords={kw}&sortBy=date_posted`, scroll, extract same shape.
  - Returns normalized `Post` list, dedup within-run by permalink, tag `source` ("feed"/"search:<kw>").
  - **No password handling.** Manual login only.
- [ ] **Step 2: Commit.** (No unit test — browser is integration; verified live below.)

### Task 3.2: ingest node (browser OR fixture) + reauth endpoint

**Files:** Create `backend/app/agent/nodes/ingest.py`, `backend/app/api/linkedin.py`; modify `backend/app/main.py` to include the router.

- [ ] **Step 1: ingest.py** — if `state["settings"]["fixture_mode"]`: load `fixtures/sample_posts.json` → `raw_posts`, log event, return. Else: `LinkedInScraper`; if not logged in → append error `"not_logged_in"`, return empty (graph stops cleanly). Else scrape feed + each keyword's search, merge, cap total, set `raw_posts`.
- [ ] **Step 2: linkedin.py router** — `POST /linkedin/reauth`: launch persistent context to `https://www.linkedin.com/login` headful and leave it open for manual login (run in background task; return `{"status":"browser_opened"}`).
- [ ] **Step 3: Fixture-path test** — `tests/test_ingest_fixture.py`: set `fixture_mode=True`, run `ingest(state)`, assert `len(raw_posts) == 8`. Run → pass. Commit.

- [ ] **MILESTONE 3 VERIFY:**
  - **Claude (offline):** fixture test passes.
  - **USER (live):** `POST /linkedin/reauth` → log into LinkedIn in the opened window → close. Then a one-off `scripts/try_ingest.py` (fixture_mode off) prints scraped feed+search posts. **User confirms real posts return before continuing.**

---

## MILESTONE 4 — Full LangGraph graph + dedup + select + /run

### Task 4.1: dedup + select nodes

**Files:** Create `backend/app/agent/nodes/dedup.py`, `backend/app/agent/nodes/select.py`; Test `backend/tests/test_dedup_select.py`

- [ ] **Step 1: Failing tests** —
  - dedup: classified contains a permalink already in `candidates`/`sent` → dropped from `deduped`; new ones kept.
  - select: from a mix, keep only `is_job==True`, sorted by `relevance_score` desc, length == min(min_posts-or-more available); if fewer than `min_posts` job posts, `errors` contains a `"low_yield"` notice and all jobs still pass through.
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: dedup.py** — query existing permalinks from `Candidate` + `Sent`; `deduped = [c for c in classified if c["post"].permalink not in existing]`.
- [ ] **Step 4: select.py** — `jobs = [c for c in deduped if c["cls"].is_job]`; sort desc by `cls.relevance_score`; `selected = jobs` (keep all jobs; UI shows top); if `len(jobs) < min_posts`: append `errors` low-yield notice.
- [ ] **Step 5: Run → pass. Commit.**

### Task 4.2: graph wiring + persistence + RunManager

**Files:** Create `backend/app/agent/graph.py`, `backend/app/runner.py`, `backend/app/agent/nodes/review_gate.py`, `backend/app/agent/nodes/deliver.py` (deliver may be a no-op logging stub until M5); Test `backend/tests/test_graph_fixture.py`

- [ ] **Step 1: graph.py** — `build_graph()` with nodes ingest→classify→dedup→select→review_gate; `review_gate` conditional edge: `auto_send` False → persist selected as `pending` Candidates + END; True → deliver. `run_pipeline(run_id)`: load settings snapshot into state, invoke graph, update `runs` row (status/posts_seen/jobs_found/error) and `run_events`.
- [ ] **Step 2: runner.py** — `RunManager.start()` creates a `Run` row (status="running"), launches `run_pipeline` as an asyncio task, guards single-active-run; `log_event(run_id, level, msg)` writes `RunEvent`.
- [ ] **Step 3: review_gate.py / deliver.py** — review_gate persists candidates (idempotent upsert on permalink). deliver (stub for now): if `dry_run`, log formatted messages to `run_events` and mark would-send.
- [ ] **Step 4: Failing test** (`test_graph_fixture.py`) — `fixture_mode=True`, monkeypatch `classify_post` stub, run `run_pipeline`; assert ≥5 `pending` candidates created, `Run.status=="finished"`, `jobs_found>=5`.
- [ ] **Step 5: Run → pass.**

### Task 4.3: runs + candidates + send API

**Files:** Create `backend/app/api/runs.py`, `backend/app/api/candidates.py`, `backend/app/api/send.py`; modify `main.py`; Test `backend/tests/test_api_run.py`

- [ ] **Step 1: Failing test** — `POST /run` (fixture_mode on) → 200 `{run_id}`; poll `GET /runs/{id}` until finished; `GET /candidates?status=pending` returns ≥5; `POST /candidates/{id}/approve` → status approved; `POST /candidates/{id}/reject` → rejected.
- [ ] **Step 2: Implement routers** — runs (POST /run via RunManager, GET list/detail incl. events), candidates (list by status, approve/reject, bulk approve), send (POST /send → calls `deliver_approved()`; in dry_run logs only).
- [ ] **Step 3: Run → pass. Commit.**

- [ ] **MILESTONE 4 VERIFY (offline):** with `fixture_mode=true, dry_run=true`, `POST /run` → review queue fills with ≥5 candidates; approve a few; `POST /send` logs the digest messages (no real send yet). **Confirm.**

---

## MILESTONE 5 — TelegramChannel + /send (needs token + chat IDs)

### Task 5.1: DeliveryChannel + formatting + Telegram

**Files:** Create `backend/app/delivery/__init__.py`, `base.py`, `formatting.py`, `telegram.py`, `whatsapp_macos.py`; Test `backend/tests/test_delivery.py`

- [ ] **Step 1: Failing tests** —
  - `format_digest(candidates)` returns a string containing each role • company • location • summary • permalink, and the count.
  - `TelegramChannel.send(chat_id, msg)` (httpx monkeypatched) POSTs to `…/bot{token}/sendMessage` with `chat_id`, `text`, `parse_mode`; returns `SendResult(ok=True)`. On HTTP error returns `SendResult(ok=False, error=...)`.
- [ ] **Step 2: Run → fail.**
- [ ] **Step 3: base.py** — `DeliveryChannel` ABC (`send`, `health`), `SendResult` dataclass, `get_channel(settings)` factory (telegram|whatsapp). formatting.py — `format_digest`, `format_individual`. telegram.py — `TelegramChannel`. whatsapp_macos.py — `WhatsAppChannel` stub: `send` raises `NotImplementedError("WhatsApp via macOS app is not yet implemented")`, `health()` returns False; documented deferred.
- [ ] **Step 4: Wire deliver node + deliver_approved()** to use `get_channel`, send per settings (digest vs individual) to each group_id, record `Sent`, mark candidates `sent`; respect `dry_run`.
- [ ] **Step 5: Run → pass. Commit.**

- [ ] **MILESTONE 5 VERIFY (live, needs user):** user creates a BotFchatter bot, adds it to a test group, provides `TELEGRAM_BOT_TOKEN` + chat IDs (Settings). With `dry_run=false`, approve candidates → `POST /send` → **confirm a digest lands in the test group**; `sent` + history recorded.

---

## MILESTONE 6 — Frontend operator console (frontend-design skill)

> Built with the `frontend-design` skill. Dark "operator console" aesthetic, one restrained accent, Lucide icons, no localStorage — all state via API. Vite proxy `/api` → `http://localhost:8000`.

### Tasks (each ends in a commit)
- [ ] **6.1 Scaffold** — `npm create vite@latest frontend -- --template react-ts`; add Tailwind, Lucide, a typed `api.ts` client wrapping all endpoints; Vite dev proxy.
- [ ] **6.2 App shell + nav** — sidebar nav (Dashboard, Review Queue, History, Settings, Activity); top banner with the LinkedIn ToS warning; status pill (idle/running/error) polling `/health` + active run.
- [ ] **6.3 Dashboard** — agent status, last run summary, "Run now" + "Send approved" buttons, today's yield, next scheduled-run countdown.
- [ ] **6.4 Review Queue (hero)** — candidate card grid: role, company, location, relevance bar, one-line summary, "view original" link, Approve/Reject toggles, bulk approve. Optimistic updates against the API.
- [ ] **6.5 History** — sent log table (channel, group, timestamp, message preview).
- [ ] **6.6 Settings** — keywords, schedule time, min posts, auto-send toggle (+warning), dry-run toggle, delivery channel selector, 3 group/chat IDs, Ollama model, "Re-authenticate LinkedIn" button (calls `/linkedin/reauth`).
- [ ] **6.7 Activity/Logs** — polls `/runs/{id}` events, live-ish log stream.

- [ ] **MILESTONE 6 VERIFY:** `npm run dev`, backend running, fixture_mode on → triage the review queue, change settings, watch a run in Activity. **Confirm.**

---

## MILESTONE 7 — APScheduler daily job + WhatsApp macOS stub

- [ ] **7.1 scheduler.py** — APScheduler `AsyncIOScheduler`; on startup schedule a daily job at `settings.schedule_time` calling `RunManager.start()`; reschedule on settings change. Job respects `auto_send`/`dry_run`.
- [ ] **7.2 WhatsApp deferred doc** — confirm `whatsapp_macos.py` stub + UI label "unofficial, macOS app automation, number-ban risk"; add a `docs/whatsapp-macos-notes.md` describing the intended `osascript`/`whatsapp://send` approach and the group-selection brittleness.
- [ ] **MILESTONE 7 VERIFY:** set schedule to ~2 min out, fixture_mode on, confirm the scheduled run fires and fills the queue. **Confirm.**

---

## MILESTONE 8 — README + ToS warnings

- [ ] **8.1 README.md** — covers: `ollama list` / `ollama pull gemma4:12b` (+ how to switch model tag), `playwright install chromium`, backend venv + install + `uvicorn`, first-run LinkedIn manual-login flow, Telegram BotFather + chat-id steps (+ WhatsApp deferred note), `npm i && npm run dev`, and the two ToS warnings stated plainly.
- [ ] **8.2 Final pass** — `/health` green, end-to-end fixture run, README accurate. Commit.

---

## Self-Review

**Spec coverage:** §1–§16 map to milestones — ingest feed+search (M3), Ollama classify (M2), dedup/select (M4), review gate + HITL (M4), Telegram digest (M5), frontend 5 views (M6), scheduler (M7), WhatsApp deferred stub (M5/M7), README + ToS (M8), data model incl. seen/run_events (M1). No gaps.

**Placeholders:** deliver node is an explicit dry-run stub in M4, completed in M5 (intentional, not a placeholder). WhatsApp stub is intentionally deferred per spec §9.

**Type consistency:** `Classification` (M2) reused in classify/select/format; `Post` (M1 schemas) used by scraper/ingest/classify; `AgentState` (M2) used by all nodes; `get_channel`/`SendResult` (M5) used by deliver node + `/send`. Consistent.

**Known typo to ignore at execution:** "BotFchatter" in M5 verify means **BotFather**.
