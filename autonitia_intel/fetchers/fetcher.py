"""
3-tier fetch: requests → cloudscraper → Playwright. Auto-escalation.
Returns raw HTML. Caching is keyed by URL with a 24h TTL.
"""

import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests

from ..config import BROWSER_HEADERS, CACHE_DIR, FETCH_RETRIES, REQUEST_TIMEOUT
from .robots import RobotsDisallowed, allowed

TTL_SECONDS = 86400
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# Container-safe Chromium flags. `--disable-dev-shm-usage` is the key one: in
# Docker the default /dev/shm is tiny (64MB) and Chromium crashes/OOMs without it.
_CHROMIUM_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--disable-extensions",
]

# Cap concurrent browser renders so parallel requests can't exhaust memory on a
# small instance. Tune with PLAYWRIGHT_MAX_CONCURRENCY (default 2).
_MAX_BROWSERS = max(1, int(os.getenv("PLAYWRIGHT_MAX_CONCURRENCY", "2")))
_browser_gate = threading.BoundedSemaphore(_MAX_BROWSERS)


def _cache_path(url: str) -> Path:
    return CACHE_DIR / f"{hashlib.sha256(url.encode()).hexdigest()[:16]}.json"


def _cache_get(url: str) -> str | None:
    p = _cache_path(url)
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    if time.time() - data["ts"] > TTL_SECONDS:
        p.unlink()
        return None
    return data["html"]


def _cache_put(url: str, html: str) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(url).write_text(json.dumps({"ts": time.time(), "url": url, "html": html}))


def _is_blocked(html: str, status: int) -> bool:
    if status in (403, 503):
        return True
    snippet = html[:3000].lower()
    return any(s in snippet for s in [
        "just a moment", "captcha", "enable javascript",
        "challenge-platform", "cf-browser-verification", "attention required",
    ])


def _is_thin(html: str, min_chars: int = 600) -> bool:
    """
    JS-rendered pages often return a near-empty shell to plain `requests`.
    If the visible text is tiny, escalate to a real browser so we don't miss
    content (addresses, WhatsApp links, etc.) that loads client-side.
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return len(soup.get_text(strip=True)) < min_chars


def _insufficient(html: str, status: int) -> bool:
    return _is_blocked(html, status) or _is_thin(html)


def _via_cloudscraper(url: str) -> str:
    import cloudscraper
    scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "darwin", "mobile": False})
    resp = scraper.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _via_playwright(url: str) -> str:
    from playwright.sync_api import sync_playwright
    # Bound concurrency, then always tear the browser down — even on error — so a
    # failed render can't leak a Chromium process and starve the instance.
    with _browser_gate, sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=_CHROMIUM_ARGS)
        try:
            ctx = browser.new_context(user_agent=BROWSER_HEADERS["User-Agent"], locale="en-US",
                                      viewport={"width": 1920, "height": 1080})
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            try:
                page.wait_for_load_state("networkidle", timeout=12_000)
            except Exception:
                pass
            page.wait_for_timeout(4000)
            return page.content()
        finally:
            browser.close()


def _tier1_with_retry(url: str) -> str | None:
    """Plain requests with exponential backoff on transient errors. None → escalate."""
    session = requests.Session()
    session.headers.update(BROWSER_HEADERS)
    for attempt in range(FETCH_RETRIES + 1):
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if resp.status_code in _RETRYABLE_STATUS and attempt < FETCH_RETRIES:
                time.sleep(0.5 * (2 ** attempt))   # 0.5s, 1s, 2s …
                continue
            if not _insufficient(resp.text, resp.status_code):
                resp.raise_for_status()
                return resp.text
            return None  # blocked/thin → escalate to cloudscraper/Playwright
        except requests.RequestException:
            if attempt < FETCH_RETRIES:
                time.sleep(0.5 * (2 ** attempt))
                continue
            return None
    return None


def fetch_html(url: str, use_cache: bool = True) -> str:
    if use_cache:
        cached = _cache_get(url)
        if cached:
            return cached

    # Politeness: respect robots.txt before any network fetch.
    if not allowed(url):
        raise RobotsDisallowed(f"robots.txt disallows fetching {url}")

    # Tier 1: requests with retry/backoff (escalate on bot-block OR thin JS shell)
    html = _tier1_with_retry(url)
    if html is not None:
        if use_cache:
            _cache_put(url, html)
        return html

    # Tier 2: cloudscraper
    try:
        html = _via_cloudscraper(url)
        if not _insufficient(html, 200):
            if use_cache:
                _cache_put(url, html)
            return html
    except Exception:
        pass

    # Tier 3: Playwright (full JS render)
    html = _via_playwright(url)
    if use_cache:
        _cache_put(url, html)
    return html
