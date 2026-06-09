"""Headful LinkedIn UI scraper (Playwright sync API).

SAFETY: never runs headless, never handles passwords. The user logs in once
manually into a persistent user-data-dir; the session persists across runs.
Human-like jitter + hard caps on scrolls and total session time keep the
footprint low. Automating LinkedIn violates its User Agreement — use sparingly.
"""
import os
import random
import time
from urllib.parse import quote

from playwright.sync_api import sync_playwright

from app.config import config
from app.schemas import Post

FEED_URL = "https://www.linkedin.com/feed/"
LOGIN_URL = "https://www.linkedin.com/login"
SEARCH_URL = "https://www.linkedin.com/search/results/content/?keywords={kw}&sortBy=%22date_posted%22"

MAX_SESSION_SECONDS = 180  # hard cap on a single scraping session
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Robust-with-fallback selectors (LinkedIn DOM is volatile).
CARD_SELECTOR = "div.feed-shared-update-v2, div.update-components-update-v2, div[data-urn*='urn:li:activity']"
TEXT_SELECTORS = [
    ".update-components-text",
    ".feed-shared-update-v2__description",
    ".feed-shared-inline-show-more-text",
    "span.break-words",
]
AUTHOR_SELECTORS = [
    ".update-components-actor__name",
    ".update-components-actor__title",
    "span.update-components-actor__name span[aria-hidden='true']",
]


def _jitter(lo: float = 2.0, hi: float = 6.0) -> None:
    time.sleep(random.uniform(lo, hi))


class LinkedInScraper:
    """Context manager around a persistent headful Chromium context."""

    def __init__(self, headless: bool = False):
        # headless is forced False; the param exists only so tests can introspect.
        self.headless = False
        self._pw = None
        self._ctx = None

    def __enter__(self) -> "LinkedInScraper":
        os.makedirs(config.aijr_user_data_dir, exist_ok=True)
        self._pw = sync_playwright().start()
        self._ctx = self._pw.chromium.launch_persistent_context(
            user_data_dir=config.aijr_user_data_dir,
            headless=False,
            viewport={"width": 1340, "height": 940},
            user_agent=USER_AGENT,
            args=["--disable-blink-features=AutomationControlled"],
        )
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self._ctx:
                self._ctx.close()
        finally:
            if self._pw:
                self._pw.stop()

    # --- internals -------------------------------------------------------
    def _page(self):
        return self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()

    @staticmethod
    def _first_text(card, selectors: list[str]) -> str:
        for sel in selectors:
            try:
                loc = card.locator(sel).first
                if loc.count() > 0:
                    txt = loc.inner_text(timeout=1500).strip()
                    if txt:
                        return txt
            except Exception:
                continue
        return ""

    def _extract(self, page, acc: dict, source: str) -> None:
        cards = page.locator(CARD_SELECTOR)
        try:
            n = cards.count()
        except Exception:
            return
        for i in range(n):
            card = cards.nth(i)
            try:
                urn = card.get_attribute("data-urn") or ""
                if "urn:li:activity" not in urn:
                    continue
                permalink = f"https://www.linkedin.com/feed/update/{urn}"
                if permalink in acc:
                    continue
                text = self._first_text(card, TEXT_SELECTORS)
                if not text:
                    continue
                author = self._first_text(card, AUTHOR_SELECTORS)
                acc[permalink] = Post(
                    author=author, text=text, permalink=permalink, source=source
                )
            except Exception:
                continue

    # --- public API ------------------------------------------------------
    def is_logged_in(self) -> bool:
        page = self._page()
        try:
            page.goto(FEED_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            return False
        _jitter()
        url = page.url
        if any(x in url for x in ("/login", "/authwall", "/checkpoint", "/uas/login")):
            return False
        try:
            return page.locator("#global-nav, div.feed-shared-update-v2").count() > 0
        except Exception:
            return "/feed" in url

    def scrape_feed(self, max_scrolls: int = 8, deadline: float | None = None) -> list[Post]:
        page = self._page()
        if "/feed" not in page.url:
            page.goto(FEED_URL, wait_until="domcontentloaded", timeout=30000)
            _jitter()
        acc: dict[str, Post] = {}
        for _ in range(max_scrolls):
            if deadline and time.time() > deadline:
                break
            self._extract(page, acc, "feed")
            page.mouse.wheel(0, random.randint(1400, 2600))
            _jitter()
        self._extract(page, acc, "feed")
        return list(acc.values())

    def search_posts(
        self, keyword: str, max_scrolls: int = 3, deadline: float | None = None
    ) -> list[Post]:
        page = self._page()
        try:
            page.goto(SEARCH_URL.format(kw=quote(keyword)), wait_until="domcontentloaded", timeout=30000)
        except Exception:
            return []
        _jitter()
        acc: dict[str, Post] = {}
        for _ in range(max_scrolls):
            if deadline and time.time() > deadline:
                break
            self._extract(page, acc, f"search:{keyword}")
            page.mouse.wheel(0, random.randint(1400, 2600))
            _jitter()
        self._extract(page, acc, f"search:{keyword}")
        return list(acc.values())


def open_for_login(max_wait_seconds: int = 300) -> None:
    """Open a headful browser at the LinkedIn login page for MANUAL login,
    and keep it open until the user closes it (or the timeout elapses).
    Runs in a worker thread (no event loop) so the sync API is safe."""
    os.makedirs(config.aijr_user_data_dir, exist_ok=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=config.aijr_user_data_dir,
            headless=False,
            viewport={"width": 1340, "height": 940},
            user_agent=USER_AGENT,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        start = time.time()
        while time.time() - start < max_wait_seconds:
            try:
                if not ctx.pages:  # user closed the window
                    break
            except Exception:
                break
            time.sleep(1)
        try:
            ctx.close()
        except Exception:
            pass
