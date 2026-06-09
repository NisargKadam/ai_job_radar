# AI Job Radar

A **fully local, human-in-the-loop agentic app** that watches LinkedIn for AI/ML/LLM/Agentic
engineering job posts, classifies them with a **local Ollama model** through an explicit
**LangGraph** pipeline, lets you approve candidates in a dark "operator console" UI, and pushes
the best ones to your Telegram groups.

Nothing leaves your machine except: LinkedIn (a real browser **you** log into), Ollama
(`localhost:11434`), and your delivery channel's API (Telegram).

---

## ⚠️ Read this first — Terms of Service

- **LinkedIn:** This app automates a real, logged-in LinkedIn session via a headful browser.
  **Automating LinkedIn violates LinkedIn's User Agreement and can get your account
  restricted or suspended.** Mitigations are built in (headful only, manual login, human-like
  jitter, scroll + session caps, low frequency) but the risk is real. Use sparingly and at your
  own risk. The app never stores your password.
- **WhatsApp (deferred / opt-in):** The WhatsApp channel would drive the macOS WhatsApp app via
  UI automation. **This is unofficial, against WhatsApp's ToS, and risks a number ban — use a
  non-primary number.** It is **not implemented yet** (Telegram is the supported channel). See
  [docs/whatsapp-macos-notes.md](docs/whatsapp-macos-notes.md).

---

## How it works

```
LangGraph pipeline (backend/app/agent/graph.py)
  ingest ──▶ classify ──▶ dedup ──▶ select ──▶ review_gate ──┬─(auto_send off)─▶ END  (review queue)
                                                              └─(auto_send on)──▶ deliver
```

- **ingest** — headful Chromium (persistent session) scrolls your feed **and** runs LinkedIn
  post-search for your keywords. (Or loads `fixtures/sample_posts.json` in *fixture mode*.)
- **classify** — local Ollama model returns strict JSON per post (is_job, role, company,
  location, seniority, relevance, summary); validated with Pydantic.
- **dedup** — skips permalinks already seen/surfaced.
- **select** — keeps job posts, sorts by relevance, flags "low yield" if under your minimum.
- **review_gate** — writes candidates to the review queue (or, if auto-send is on, delivers).
- **deliver** — formats a digest (or individual messages) and sends to your 3 groups via Telegram.

Stack: **FastAPI · LangGraph · SQLAlchemy/SQLite · Playwright · Ollama** (backend) and
**React + Vite + TypeScript + Tailwind** (frontend).

---

## Prerequisites

- **Python 3.11+** (developed on 3.13)
- **Node 18+** (developed on Node 26)
- **[Ollama](https://ollama.com)** running locally, with a model pulled (default `gemma4:12b`)

```bash
ollama list                 # see what you already have
ollama pull gemma4:12b      # pull the default classifier if needed
```

> **Switching models:** any chat model in `ollama list` works. Change it in the UI
> (Settings → Ollama model) or in the `settings` table. A smaller/faster tag (e.g. a 4B model)
> trades some accuracy for speed.

---

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/playwright install chromium      # installs the headful browser

cp .env.example .env                          # then edit .env (Telegram token, optional)

./.venv/bin/uvicorn app.main:app --port 8000 --reload
```

Backend is now on **http://localhost:8000** (`/docs` for the API, `/health` for status).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The dev server proxies `/api` → `http://localhost:8000`.

### 3. Log into LinkedIn (once)

You must log in manually — the app never handles your password. Either:

- In the UI: **Settings → Re-authenticate LinkedIn**, **or**
- From the terminal: `cd backend && ./.venv/bin/python scripts/try_login.py`

A real browser window opens. Log in normally (handle any 2FA), then **close the window**. Your
session is saved in `backend/.user-data/` and reused on every run. Verify scraping with:

```bash
cd backend && ./.venv/bin/python scripts/try_ingest.py
```

### 4. Telegram delivery

1. In Telegram, message **@BotFather** → `/newbot` → follow prompts → copy the **bot token**.
2. Put the token in `backend/.env` as `TELEGRAM_BOT_TOKEN=...` and restart the backend.
3. **Add your bot to each target group** (and make it an admin for channels).
4. Get each **chat ID**: send any message in the group, then open
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` and read `result[].message.chat.id`.
   Group IDs are negative (supergroups look like `-1001234567890`). (Tools like **@RawDataBot**
   also report chat IDs.)
5. In the UI: **Settings → Target group / chat IDs** (one per line) → **Save**.
6. Keep **Dry-run on** while testing — `Send approved` will log the message instead of sending.
   Turn Dry-run off to deliver for real.

---

## Daily use

1. **Settings** — set keywords, schedule time, min posts/day, Ollama model, delivery groups.
2. **Run now** (Dashboard) — scrapes + classifies; candidates land in the **Review Queue**.
3. **Review Queue** — Approve / Reject each card (or **Approve all**); triage in seconds.
4. **Send approved** — delivers approved jobs to your groups (respects Dry-run).
5. **Scheduler** — a daily run fires at your configured time. With **Auto-send** on, scheduled
   runs deliver without review (a warning is shown — leave it off unless you mean it).
6. **History / Activity** — see what was sent and watch live run telemetry.

**Fixture mode** (Settings) runs the whole pipeline on bundled sample posts without opening the
browser — handy for trying the app or demoing without touching LinkedIn.

---

## Verification helper scripts (`backend/scripts/`)

```bash
./.venv/bin/python scripts/try_classify.py   # classify sample posts with your Ollama model
./.venv/bin/python scripts/try_login.py      # open browser for manual LinkedIn login
./.venv/bin/python scripts/try_ingest.py     # scrape your live feed + search and print results
```

## Tests

```bash
cd backend && ./.venv/bin/pytest -q          # 24 tests (DB, classify, pipeline, delivery, API, scheduler)
```

## Configuration reference

`.env` (process-level secrets/paths):

| var | default | meaning |
|-----|---------|---------|
| `TELEGRAM_BOT_TOKEN` | _(empty)_ | BotFather token for delivery |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | local Ollama endpoint |
| `AIJR_DB_URL` | `sqlite:///./aijr.db` | SQLite database |
| `AIJR_USER_DATA_DIR` | `./.user-data` | persistent browser/login profile |

Everything else (keywords, schedule, min posts, auto-send, dry-run, channel, group IDs, model,
fixture mode, digest-vs-individual) lives in the **Settings** UI / `settings` table.

## Project structure

```
backend/    FastAPI + LangGraph + Playwright + Ollama + SQLite
  app/agent/        graph.py + nodes/ (ingest, classify, dedup, select, review_gate, deliver)
  app/llm/          ollama_client.py
  app/scraper/      linkedin.py (headful, persistent session)
  app/delivery/     base, telegram, whatsapp_macos (stub), formatting
  app/api/          health, settings, runs, candidates, send, history, linkedin
  app/scheduler.py  APScheduler daily job
  fixtures/         sample_posts.json
  scripts/          try_login / try_ingest / try_classify
  tests/
frontend/   React + Vite + TS + Tailwind operator console
docs/       design spec, implementation plan, WhatsApp notes
```
