import json
import pathlib
import time

from app.agent.nodes import log_event
from app.agent.state import AgentState
from app.schemas import Post
from app.scraper.linkedin import MAX_SESSION_SECONDS, LinkedInScraper

FIXTURE = pathlib.Path(__file__).resolve().parents[3] / "fixtures" / "sample_posts.json"


def ingest(state: AgentState) -> dict:
    settings = state.get("settings", {})
    run_id = state.get("run_id")
    errors = list(state.get("errors", []))

    if settings.get("fixture_mode"):
        posts = [Post(source="fixture", **p) for p in json.loads(FIXTURE.read_text())]
        log_event(run_id, f"fixture_mode: loaded {len(posts)} posts")
        return {"raw_posts": posts, "errors": errors}

    keywords = settings.get("keywords", [])
    posts: dict[str, Post] = {}
    try:
        with LinkedInScraper(headless=False) as sc:
            if not sc.is_logged_in():
                errors.append("not_logged_in")
                log_event(run_id, "Not logged into LinkedIn — open Settings → Re-authenticate.", "error")
                return {"raw_posts": [], "errors": errors}

            deadline = time.time() + MAX_SESSION_SECONDS
            for p in sc.scrape_feed(max_scrolls=8, deadline=deadline):
                posts[p.permalink] = p
            log_event(run_id, f"feed: collected {len(posts)} posts")

            for kw in keywords:
                if time.time() > deadline:
                    log_event(run_id, "session time cap reached; stopping search", "warn")
                    break
                for p in sc.search_posts(kw, max_scrolls=3, deadline=deadline):
                    posts.setdefault(p.permalink, p)
            log_event(run_id, f"feed+search total: {len(posts)} unique posts")
    except Exception as e:
        errors.append(f"ingest_failed:{e}")
        log_event(run_id, f"ingest failed: {e}", "error")

    return {"raw_posts": list(posts.values()), "errors": errors}
