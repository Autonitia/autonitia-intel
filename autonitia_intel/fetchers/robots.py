"""
robots.txt awareness — polite, opt-out crawling.

Before fetching, we check the target's robots.txt for our agent. Results are
cached per-domain. If robots.txt is missing/unreachable we default to ALLOW
(standard behaviour). Disabled with AUTONITIA_RESPECT_ROBOTS=false.
"""

from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

from ..config import BROWSER_HEADERS, RESPECT_ROBOTS, ROBOTS_UA

_CACHE: dict[str, RobotFileParser | None] = {}


class RobotsDisallowed(Exception):
    """Raised when robots.txt disallows fetching a URL."""


def _parser_for(domain_root: str) -> RobotFileParser | None:
    if domain_root in _CACHE:
        return _CACHE[domain_root]
    rp = RobotFileParser()
    try:
        resp = requests.get(f"{domain_root}/robots.txt", headers=BROWSER_HEADERS, timeout=8)
        if resp.status_code >= 400:
            rp = None  # no robots.txt → allow all
        else:
            rp.parse(resp.text.splitlines())
    except requests.RequestException:
        rp = None
    _CACHE[domain_root] = rp
    return rp


def allowed(url: str) -> bool:
    """True if we may fetch this URL (always True when robots respect is off)."""
    if not RESPECT_ROBOTS:
        return True
    parsed = urlparse(url)
    if not parsed.scheme:
        return True
    root = f"{parsed.scheme}://{parsed.netloc}"
    rp = _parser_for(root)
    if rp is None:
        return True
    return rp.can_fetch(ROBOTS_UA, url)
