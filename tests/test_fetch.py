"""Unit tests for robots.txt awareness + retry (no real network)."""

import pytest

from autonitia_intel.fetchers import robots
from autonitia_intel.fetchers import fetcher
from autonitia_intel.fetchers.robots import RobotsDisallowed


class _FakeResp:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


_ROBOTS = "User-agent: *\nDisallow: /private\n"


@pytest.fixture(autouse=True)
def _clear_cache():
    robots._CACHE.clear()
    yield
    robots._CACHE.clear()


def test_disallowed_path(monkeypatch):
    monkeypatch.setattr(robots, "RESPECT_ROBOTS", True)
    monkeypatch.setattr(robots.requests, "get", lambda *a, **k: _FakeResp(_ROBOTS, 200))
    assert robots.allowed("https://x.com/private/secret") is False
    assert robots.allowed("https://x.com/public/page") is True


def test_missing_robots_allows(monkeypatch):
    monkeypatch.setattr(robots, "RESPECT_ROBOTS", True)
    monkeypatch.setattr(robots.requests, "get", lambda *a, **k: _FakeResp("", 404))
    assert robots.allowed("https://x.com/anything") is True


def test_respect_off_allows_everything(monkeypatch):
    monkeypatch.setattr(robots, "RESPECT_ROBOTS", False)
    # even a disallow rule is ignored
    monkeypatch.setattr(robots.requests, "get", lambda *a, **k: _FakeResp(_ROBOTS, 200))
    assert robots.allowed("https://x.com/private/secret") is True


def test_fetch_html_raises_when_disallowed(monkeypatch):
    monkeypatch.setattr(fetcher, "allowed", lambda url: False)
    with pytest.raises(RobotsDisallowed):
        fetcher.fetch_html("https://x.com/blocked", use_cache=False)


def test_tier1_retries_then_gives_up(monkeypatch):
    calls = {"n": 0}

    class _Sess:
        headers = {}
        def get(self, *a, **k):
            calls["n"] += 1
            return _FakeResp("", 503)   # always transient

    monkeypatch.setattr(fetcher.requests, "Session", lambda: _Sess())
    monkeypatch.setattr(fetcher.time, "sleep", lambda *_: None)  # no real backoff wait
    monkeypatch.setattr(fetcher, "FETCH_RETRIES", 2)
    assert fetcher._tier1_with_retry("https://x.com") is None
    assert calls["n"] == 3   # 1 initial + 2 retries
