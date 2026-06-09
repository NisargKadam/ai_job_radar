"""Manual verification for Milestone 3 (LIVE LinkedIn — run by the user).

Opens your persistent LinkedIn session, scrapes the feed + keyword search, and
prints what it found. If you are not logged in, it will tell you to run the
re-auth flow first.

    cd backend
    ./.venv/bin/python scripts/try_ingest.py

Tip: run scripts/try_login.py first (or POST /linkedin/reauth) to log in once.
"""
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.db.models import DEFAULT_KEYWORDS  # noqa: E402
from app.scraper.linkedin import MAX_SESSION_SECONDS, LinkedInScraper  # noqa: E402

KEYWORDS = DEFAULT_KEYWORDS[:3]  # keep it light for a manual check


def main() -> None:
    with LinkedInScraper(headless=False) as sc:
        if not sc.is_logged_in():
            print("NOT LOGGED IN. Run: ./.venv/bin/python scripts/try_login.py  (log in, then close window)")
            return
        print("Logged in. Scraping feed...")
        deadline = time.time() + MAX_SESSION_SECONDS
        feed = sc.scrape_feed(max_scrolls=6, deadline=deadline)
        print(f"  feed: {len(feed)} posts")
        seen = {p.permalink for p in feed}
        search_total = 0
        for kw in KEYWORDS:
            if time.time() > deadline:
                break
            res = [p for p in sc.search_posts(kw, max_scrolls=2, deadline=deadline) if p.permalink not in seen]
            seen.update(p.permalink for p in res)
            search_total += len(res)
            print(f"  search '{kw}': +{len(res)} new")
        allposts = list(seen)
        print(f"\nTOTAL unique posts: {len(allposts)}")
        for p in (feed + [])[:5]:
            print(f"\n--- [{p.source}] {p.author[:50]}")
            print(f"    {p.text[:160].replace(chr(10), ' ')}")
            print(f"    {p.permalink}")


if __name__ == "__main__":
    main()
