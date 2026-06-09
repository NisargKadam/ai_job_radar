# AI Job Radar — Design Spec

**Date:** 2026-06-09
**Status:** Approved (user said "let's build it" after design walkthrough)

## 1. Purpose

A **fully local, human-in-the-loop agentic application** that:

1. Opens LinkedIn in a real (headful) browser session the user logged into manually.
2. Collects posts by scrolling the home feed **and** running LinkedIn's post/content search for configured keywords.
3. Uses a **local Ollama model** to classify which posts are genuine AI/Agentic-Engineer job opportunities and extract structured fields.
4. De-duplicates against history.
5. Presents top candidates in a dashboard for **one-click approval**.
6. On approval (or scheduled auto-send if enabled) sends **≥5** formatted job posts to **3 groups** via a pluggable delivery channel (Telegram default; WhatsApp deferred).

## 2. Hard constraints

- **100% local.** No cloud LLM calls. External network limited to: LinkedIn (browser), Ollama (`localhost:11434`), and the delivery channel's API.
- **LLM = Ollama**, model from settings (`gemma4:12b`, confirmed present locally). Structured output via `format:"json"`, validated with Pydantic v2.
- **LinkedIn access = UI scraping only.** No LinkedIn developer/API account. Headful Chromium via Playwright, persistent user-data-dir (manual login once, session persists), randomized 2–6s human-like jitter, scroll cap + hard session-time cap, **never headless**, **never store the password**.
- **Human-in-the-loop by default.** Pipeline fills a review queue; nothing sends without explicit approval unless `auto_send` is toggled on.
- **Delivery is a pluggable interface.** `DeliveryChannel.send(group_id, message)`. `TelegramChannel` implemented now. `WhatsAppChannel` deferred.
- **Idempotent + dedup.** Persist seen permalinks; never send the same link twice.
- **Dry-run mode.** Global toggle: runs the full pipeline but logs the outbound message instead of sending.

## 3. Environment (verified 2026-06-09)

- Python 3.13.12, Node v26.0.0 / npm 11.12.1, Ollama 0.30.6.
- Ollama models present: `gemma4:12b` (the configured classifier), `qwen2.5-coder:7b`, `nomic-embed-text`, `x/flux2-klein`.
- Project root = working directory `LinkedIn_Job_Posts/` (empty, dedicated). Build directly in it (no extra `ai-job-radar/` nesting).

## 4. Tech stack

- **Backend:** Python 3.11+ (3.13 present), FastAPI, Uvicorn, APScheduler, SQLAlchemy + SQLite, Pydantic v2.
- **Agent orchestration:** LangGraph state machine (the explicit, readable core).
- **Browser:** Playwright (Chromium, headful, persistent context).
- **LLM client:** httpx → Ollama REST (`/api/generate` or `/api/chat`) with `format:"json"`.
- **Frontend:** React + Vite + TypeScript + Tailwind, Lucide icons, dark "operator console" aesthetic, built with the `frontend-design` skill. No localStorage/sessionStorage — all state via the API.
- **WhatsApp (deferred):** macOS WhatsApp desktop app automation (see §9), not whatsapp-web.js.

## 5. Process topology

- **`backend/`** — one FastAPI/Uvicorn process hosting: REST API, APScheduler daily job, the LangGraph pipeline, the Playwright headful browser (persistent user-data-dir, launched on demand), the Ollama client, and SQLite via SQLAlchemy.
- **`frontend/`** — Vite React TS + Tailwind; polls the API for run status; no client-side storage.
- WhatsApp automation lives inside the backend (`delivery/whatsapp_macos.py`) — no separate service.

## 6. Run execution model

`POST /run` enqueues a run and executes it in a background asyncio task, returning `run_id` immediately. Progress is written to `runs` + a `run_events` log table. Frontend polls `GET /runs/{id}`. Rationale: ingest drives a headful browser for minutes; the API must stay responsive and the Activity view needs a progress trail. Only one run may be active at a time (guarded).

## 7. LangGraph pipeline

`AgentState = { raw_posts, classified, deduped, selected, errors, run_id, dry_run, auto_send, settings }`

Nodes:

1. **ingest** — persistent-context headful Chromium. Two sub-sources, merged & normalized to `Post{author, text, permalink, timestamp, source}`:
   - (a) scroll home feed N times with 2–6s jitter;
   - (b) for each keyword, scrape LinkedIn's **post/content search** results.
   Not-logged-in detected via login redirect / missing feed → set error, stop cleanly, surface "Re-authenticate" prompt. Hard caps on scroll count **and** total session seconds. Robust selectors with graceful fallback.
   **Fixture mode** (`settings.fixture_mode` / env): load posts from a local JSON fixture instead of launching the browser — enables full offline verification of the rest of the pipeline.
2. **classify** — for each post, prompt Ollama with `format:"json"` and a strict schema:
   `{ "is_job": bool, "role_title": str|null, "company": str|null, "location": str|null, "seniority": str|null, "relevance_score": 0-1, "one_line_summary": str|null }`.
   Keywords passed into the prompt for keyword + semantic judgment. Validate with Pydantic; one stricter retry on malformed JSON, then drop + log. Cost guard: skip the LLM for permalinks already in the `seen` ledger (mark them so dedup drops them).
3. **dedup** — drop permalinks already present in `candidates` or `sent`.
4. **select** — keep `is_job == true`, sort by `relevance_score` desc, take top `min_posts` (allow more). If fewer than `min_posts`, set a "low yield today" notice rather than padding with junk.
5. **review_gate** — conditional edge: `auto_send` OFF → upsert selected candidates as `pending`, END. ON → continue to deliver.
6. **deliver** — format each selected job (role • company • location • summary • link), send to each of the 3 groups via `DeliveryChannel.send`, record to `sent`, mark candidates `sent`. Respects `dry_run` (logs instead of sends).

`/send` runs the **deliver path on already-approved candidates** as a standalone call — not a full graph re-run and not LangGraph's checkpointer/interrupt. Matches the "approve later, then push" HITL flow and keeps the graph simple.

## 8. Data model (SQLite)

- `runs` (id, started_at, finished_at, status, posts_seen, jobs_found, sent_count, error)
- `candidates` (id, run_id, permalink UNIQUE, author, role_title, company, location, seniority, relevance_score, summary, raw_text, status[pending|approved|rejected|sent], created_at)
- `sent` (id, candidate_id, channel, group_id, sent_at, message)
- `settings` (singleton: keywords, schedule_time, min_posts, auto_send bool, dry_run bool, delivery_channel, group_ids json, ollama_model, fixture_mode bool)
- **`seen`** (permalink UNIQUE, first_seen_run_id, created_at) — lightweight ledger so we never re-classify/re-surface a link, even non-jobs.
- **`run_events`** (id, run_id, ts, level, message) — timestamped log lines for the Activity view.

## 9. Delivery channels

- **`DeliveryChannel` ABC:** `send(group_id, message) -> SendResult`, `health() -> bool`.
- **`TelegramChannel` (default):** Bot API `sendMessage`, HTML parse mode. Bot token from `.env`; `group_id` = chat IDs from settings. README documents BotFather + chat-id retrieval.
  - **Default message format:** one **digest per group** listing the approved jobs (role • company • location • summary • link), rather than 5×3 individual messages. Settings toggle switches to individual messages.
- **`WhatsAppChannel` (deferred):** drives the **macOS WhatsApp desktop app** via AppleScript/`osascript` UI automation and/or the `whatsapp://send?...` URL scheme, called from Python (`delivery/whatsapp_macos.py`). Shipped now only as the interface stub. UI + README label it **unofficial, against WhatsApp ToS, risk of number ban — use a non-primary number.** Known challenge (to harden when built): reliable group selection via UI scripting is brittle.

## 10. Secrets & config

- `.env` holds only `TELEGRAM_BOT_TOKEN` (+ optional overrides). `.env.example` documents it.
- Everything else lives in the `settings` table: keywords, schedule_time, min_posts, auto_send, dry_run, delivery_channel, group_ids (json), ollama_model, fixture_mode.
- Ask the user for the bot token + 3 chat IDs only at the delivery milestone.

## 11. API (FastAPI)

- `POST /run` — enqueue pipeline now → `{run_id}`.
- `GET /runs`, `GET /runs/{id}` (includes events).
- `GET /candidates?status=pending` — review queue.
- `POST /candidates/{id}/approve`, `POST /candidates/{id}/reject`, bulk approve.
- `POST /send` — send all approved-pending candidates now.
- `GET /settings`, `PUT /settings`.
- `POST /linkedin/reauth` — launch headful browser for manual login.
- `GET /health` — reports Ollama reachable, browser session valid, delivery channel configured.

## 12. Frontend (operator console)

Single-page app, dark theme, one restrained accent, real typographic hierarchy, generous spacing, Lucide icons. Views:

- **Dashboard** — agent status (idle/running/error), last run summary, "Run now" + "Send approved", today's yield, next scheduled run countdown.
- **Review Queue (hero)** — card grid of pending candidates: role, company, location, relevance bar, one-line summary, "view original" link, Approve/Reject toggles, bulk approve. Triage in ~30s.
- **History** — sent log with channel + group + timestamp.
- **Settings** — keywords, schedule time, min posts, auto-send toggle (+warning), dry-run toggle, delivery channel selector, 3 group/chat IDs, Ollama model, "Re-authenticate LinkedIn" button.
- **Activity/Logs** — live-ish run log from `run_events`.

## 13. Safety / ToS

- Headful only (no headless), persistent user-data-dir (manual login, password never stored), randomized jitter, scroll + session-time caps, low frequency.
- Prominent in-app banner **and** README warnings:
  - **LinkedIn:** automation violates LinkedIn's User Agreement; risk of restriction/suspension. Keep frequency low; manual login required.
  - **WhatsApp:** macOS-app automation is unofficial and against WhatsApp ToS; risk of number ban — use a non-primary number.

## 14. Project structure

```
LinkedIn_Job_Posts/
  backend/
    app/
      main.py
      config.py
      scheduler.py
      api/            (routers)
      agent/
        graph.py
        state.py
        nodes/        (ingest, classify, dedup, select, review_gate, deliver)
      llm/ollama_client.py
      scraper/linkedin.py
      delivery/       (base.py, telegram.py, whatsapp_macos.py)
      db/             (models.py, session.py)
    fixtures/         (sample_posts.json)
    requirements.txt
    .env.example
  frontend/           (Vite React TS + Tailwind)
  docs/superpowers/specs/
  README.md
```

## 15. Build order (verify each step runs)

1. Backend scaffold + DB models + settings + `/health` → run.
2. Ollama client + `classify` node on a fixture post → confirm valid JSON → run.
3. Playwright `ingest` + persistent context + manual-login/re-auth flow + fixture mode (Claude verifies fixture path; **user** verifies live LinkedIn) → run.
4. Full LangGraph graph + dedup + select; `POST /run` end-to-end into review queue (dry-run on, fixture source) → Claude verifies offline → run.
5. `TelegramChannel` + `/send` → user provides token + chat IDs, confirms a test message lands → run.
6. Frontend (frontend-design skill): Dashboard → Review Queue → Settings → History → Activity → run against live API.
7. APScheduler daily job + `WhatsAppChannel` macOS stub.
8. README with full setup + inline ToS warnings.

## 16. Definition of done

- User logs into LinkedIn once; session persists.
- "Run now" collects feed + search posts, classifies locally with Ollama, dedups, fills the review queue with ≥5 AI-job candidates on a normal day.
- User approves in the UI and pushes to 3 Telegram groups; history records it.
- Daily schedule works; dry-run and auto-send toggles behave correctly.
- WhatsApp available as opt-in (deferred build) with risk surfaced.
- UI is something an engineer wants to open every morning.

## 17. Decisions made on the user's behalf (easy to revisit)

- Telegram default = **digest per group** (not 5×3 individual messages).
- Added `seen` + `run_events` tables beyond the original four.
- Run executes as a **background task**; `/send` is a standalone deliver path.
- WhatsApp (deferred) drives the **macOS WhatsApp app** via `osascript`, not whatsapp-web.js (per user constraint).
