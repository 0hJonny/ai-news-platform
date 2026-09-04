"""CyberNewsSource — the Source for cybernews.com (config.py's SOURCES
entry with name="CyberNews"). Everything specific to this site — how its
listing pages paginate (/page/{n}), which selectors hold article links,
which selectors/JSON-LD hold article content — lives entirely in this one
class. producer.py/tasks.py never see any of it; they only call
discover()/fetch_article().
"""

import itertools
import json
import logging
import random

import cloudscraper
from bs4 import BeautifulSoup

from .base import DiscoveredArticle

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15
_PLATFORMS = ["linux", "windows", "darwin", "android"]
_BROWSERS = ["chrome", "firefox"]


class CyberNewsSource:
    def __init__(self):
        # A plain requests.get() 403s on cybernews.com (Cloudflare
        # bot-check). One scraper per Source instance — get_parser() hands
        # out a fresh instance per call, so this never gets shared across
        # concurrent Celery tasks; the Cloudflare-challenge solve has real
        # per-instance setup cost, no need to redo it per request either.
        self._scraper = cloudscraper.create_scraper(
            delay=6,
            browser={"browser": random.choice(_BROWSERS), "platform": random.choice(_PLATFORMS)},
        )

    def _fetch_html(self, url: str) -> str:
        response = self._scraper.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text

    def discover(self, listing_url: str, language_code: str):
        """Walks /page/{n} pagination — cybernews-specific, nothing outside
        this class knows this shape exists. A fetch failure or an empty
        page (no more links) both just end the generator; producer.py
        treats "stopped early" and "ran out of pages" the same way.
        """
        for page_number in itertools.count(1):
            url = f"{listing_url}/page/{page_number}" if page_number > 1 else listing_url
            try:
                html = self._fetch_html(url)
            except Exception as exc:
                logger.error("[CyberNewsSource] Failed to fetch listing %s: %s", url, exc)
                return

            links = self._extract_article_links(html)
            if not links:
                logger.info("[CyberNewsSource] %s: no article links found, stopping", url)
                return

            for link in links:
                yield DiscoveredArticle(url=link, language_code=language_code)

    def fetch_article(self, url: str) -> dict:
        # Deliberately doesn't catch: tasks.py's scrape_source needs the
        # real exception to log a useful PARSING-stage failure reason
        # instead of a generic placeholder.
        html = self._fetch_html(url)
        return self._parse_article(html)

    def _extract_article_links(self, html: str) -> list[str]:
        """Category listing pages group posts under a `cells_space_xl`
        container; individual links show up either as a dedicated
        `focus-articles__link` anchor or as the parent `<a>` of an
        `h3.heading`.
        """
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

    def _parse_article(self, html: str) -> dict:
        """(title, author) prefer JSON-LD (see _parse_json_ld) and fall back
        to CSS-based heuristics only where that came up empty. Body text
        always comes from the CSS side: JSON-LD's NewsArticle node here
        doesn't carry articleBody, only metadata.

        Body is scoped to the nearest <article>/.content container rather
        than the whole page — a page-wide <p> search also picks up
        header/footer/nav boilerplate (copyright notices, menu text) sitting
        outside the actual article, which is exactly what showed up in early
        test runs. Falls back to the whole page if no such container exists.
        """
        soup = BeautifulSoup(html, "lxml")

        title, author = self._parse_json_ld(soup)

        if not title:
            title_tag = soup.find("h1") or soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else None

        if not author:
            author_tag = soup.find(attrs={"rel": "author"}) or soup.find(
                class_=lambda c: bool(c) and "author" in c.lower()
            )
            author = author_tag.get_text(strip=True) if author_tag else "Unknown"

        container = soup.find("article") or soup.find("div", class_="content") or soup
        paragraphs = container.find_all("p")
        body = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        return {"title": title, "author": author, "body": body}

    @staticmethod
    def _parse_json_ld(soup: BeautifulSoup) -> tuple[str | None, str | None]:
        """Best-effort (title, author) from schema.org JSON-LD (Article/
        NewsArticle/BlogPosting), which most modern news sites embed for SEO.
        Far less fragile than scraping CSS classes — cybernews.com's own
        article-info__link/article-info__date/heading classes have already
        drifted out from under a redesign once, while its JSON-LD block
        hasn't. Returns (None, None) on any failure/absence so the caller
        falls back to the CSS-based heuristics above.
        """
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (json.JSONDecodeError, TypeError):
                continue

            # Sites either wrap everything in a single {"@graph": [...]} node
            # (cybernews.com's pattern) or emit a plain list/object directly.
            if isinstance(data, dict):
                nodes = data.get("@graph", [data])
            else:
                nodes = data
            if not isinstance(nodes, list):
                continue

            nodes_by_id = {n["@id"]: n for n in nodes if isinstance(n, dict) and n.get("@id")}

            for node in nodes:
                if not isinstance(node, dict):
                    continue
                node_type = node.get("@type")
                types = node_type if isinstance(node_type, list) else [node_type]
                if not any(t in ("Article", "NewsArticle", "BlogPosting") for t in types):
                    continue

                title = node.get("headline")

                author_ref = node.get("author")
                author = None
                if isinstance(author_ref, dict):
                    author = author_ref.get("name")
                    if author is None and "@id" in author_ref:
                        author_node = nodes_by_id.get(author_ref["@id"])
                        if author_node:
                            author = author_node.get("name")
                elif isinstance(author_ref, str):
                    author = author_ref

                if title or author:
                    return title, author

        return None, None
