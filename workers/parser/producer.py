"""Stage 5: producer — walks each configured CyberNews category listing
page, discovers individual article links, and for every genuinely new one
reserves a draft via the Go API and enqueues parsing.scrape_source to
actually fetch+parse it.

The listing pages in config.py's SOURCES (e.g. https://cybernews.com/crypto)
are category pages, not articles — they need to be crawled for article
links first. Link extraction below reuses the same selectors
parsers/cybewnews/cyber_news_producer.py already uses for this site
(focus-articles__link + h3.heading), just without that class's
JWT-login/BaseParser plumbing — this producer talks to the new
unauthenticated /p/articles/* ingest routes and hands work to Celery
instead of doing anything synchronously itself.

Run manually, or wire into cron the same way the old main.py was:
    python producer.py
"""

import itertools
import logging
import os
import random

import cloudscraper
import requests
from bs4 import BeautifulSoup

from config import SOURCES
from tasks import scrape_source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GOLANG_API = os.environ.get("GOLANG_API", "http://news:5000/api/v1")
REQUEST_TIMEOUT = 15

_PLATFORMS = ["linux", "windows", "darwin", "android"]
_BROWSERS = ["chrome", "firefox"]

# Same Cloudflare-bypass technique tasks.py uses — a plain requests.get()
# 403s on these listing pages too.
_scraper = cloudscraper.create_scraper(
    delay=6,
    browser={"browser": random.choice(_BROWSERS), "platform": random.choice(_PLATFORMS)},
)


def _fetch_html(url: str) -> str | None:
    try:
        response = _scraper.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text
    except Exception as exc:
        logger.error("[producer] Failed to fetch listing %s: %s", url, exc)
        return None


def _extract_article_links(html: str) -> list[str]:
    """Same post-container/link selectors as CyberNewsProducer.start()."""
    soup = BeautifulSoup(html, "lxml")
    posts_container = soup.find("div", class_="cells_space_xl")
    if not posts_container:
        return []
    posts_container = posts_container.parent

    links = []
    for a in posts_container.find_all("a", class_="focus-articles__link"):
        href = a.get("href")
        if href:
            links.append(href)
    for h3 in posts_container.find_all("h3", class_="heading"):
        parent_a = h3.parent
        if parent_a and parent_a.name == "a":
            href = parent_a.get("href")
            if href:
                links.append(href)
    return links


def _create_draft(source_link: str, language_code: str) -> tuple[str | None, bool]:
    """Returns (article_id, is_new). is_new is False both on a 409 (some
    earlier run already has this source_link) and on any request failure —
    either way, the caller shouldn't enqueue a fresh scrape for it.
    """
    try:
        response = requests.post(
            f"{GOLANG_API}/p/articles",
            json={"source_link": source_link, "language_code": language_code},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.error("[producer] Failed to create draft for %s: %s", source_link, exc)
        return None, False

    if response.status_code == 201:
        return response.json().get("data", {}).get("id"), True
    if response.status_code == 409:
        return response.json().get("data", {}).get("id"), False

    logger.error(
        "[producer] Unexpected response creating draft for %s: %s %s",
        source_link,
        response.status_code,
        response.text,
    )
    return None, False


def _walk_listing(listing_url: str, language_code: str) -> tuple[int, int]:
    """Paginates a category listing page, creating a draft for every
    article link found and enqueueing parsing.scrape_source for the ones
    that are genuinely new. Stops once a whole page comes back with
    nothing new (mirrors the old CyberNewsProducer's max_duplicates
    early-stop) — no page-count cap: this crawls newest-first, so the only
    time it ever goes deep is the first run against a source (everything is
    new); every run after that hits already-known links within the first
    page or two and stops there on its own. There's no need to keep
    reaching further into old articles — the goal here is catching new
    content for annotation, not building a historical archive.
    """
    new_count = 0
    enqueued_count = 0

    for page_number in itertools.count(1):
        url = f"{listing_url}/page/{page_number}" if page_number > 1 else listing_url
        html = _fetch_html(url)
        if not html:
            break

        links = _extract_article_links(html)
        if not links:
            logger.info("[producer] %s: no article links found, stopping", url)
            break

        page_had_new = False
        for link in links:
            article_id, is_new = _create_draft(link, language_code)
            if not article_id or not is_new:
                continue

            page_had_new = True
            new_count += 1
            scrape_source.delay(article_id, link)
            enqueued_count += 1
            logger.info("[producer] Enqueued parsing.scrape_source(%s, %s)", article_id, link)

        if not page_had_new:
            logger.info("[producer] %s: nothing new on this page, stopping pagination", listing_url)
            break

    return new_count, enqueued_count


def run():
    total_new = 0
    total_enqueued = 0

    for source in SOURCES:
        language_code = source["language_code"]
        for listing_url in source["urls"]:
            new_count, enqueued_count = _walk_listing(listing_url, language_code)
            total_new += new_count
            total_enqueued += enqueued_count

    logger.info("[producer] Done: %d new article(s), %d enqueued", total_new, total_enqueued)


if __name__ == "__main__":
    run()
