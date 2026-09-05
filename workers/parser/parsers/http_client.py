"""HttpClient — the network-layer interface a Source fetches pages through.

Kept separate from Source so how a site is fetched (plain requests vs a
Cloudflare-bypassing scraper vs, eventually, something else entirely) is
swappable independently of how a site's HTML is discovered/parsed. A Source
receives a ready HttpClient via __init__ (see registry.py, the composition
root) instead of constructing one itself — that's what lets tests hand it a
fake client, and what stops CyberNewsSource's fetch logic from being wedded
to cloudscraper specifically.
"""

import random
from typing import Protocol

import cloudscraper

_PLATFORMS = ["linux", "windows", "darwin", "android"]
_BROWSERS = ["chrome", "firefox"]

DEFAULT_TIMEOUT = 15


class HttpClient(Protocol):
    def get(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Fetch url and return the response body as text. Raises on a
        network failure or non-2xx status."""
        ...


class CloudscraperHttpClient:
    """A plain requests.get() 403s on Cloudflare-protected sites (e.g.
    cybernews.com). cloudscraper solves the bot-check challenge instead.
    One scraper per instance: get_parser() hands out a fresh Source (and
    so a fresh client) per call, so this never gets shared across
    concurrent Celery tasks — the challenge-solve has real per-instance
    setup cost, no need to redo it per request either.
    """

    def __init__(self, delay: int = 6):
        self._scraper = cloudscraper.create_scraper(
            delay=delay,
            browser={"browser": random.choice(_BROWSERS), "platform": random.choice(_PLATFORMS)},
        )

    def get(self, url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        response = self._scraper.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
