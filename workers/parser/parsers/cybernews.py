"""CyberNewsSource — the Source for cybernews.com (config.py's SOURCES
entry with name="CyberNews"). Everything specific to this site — how its
listing pages paginate (/page/{n}), which selectors hold article links,
which selectors hold article content — lives entirely in this one class.
producer.py/tasks.py never see any of it; they only call
discover()/fetch_article(). Fetching itself is delegated to an injected
HttpClient (see http_client.py) rather than built here, so this class
doesn't need to know cybernews.com happens to sit behind Cloudflare.
"""

import itertools
import logging

from bs4 import BeautifulSoup

from .base import DiscoveredArticle, JsonLdMixin
from .http_client import HttpClient

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15


class CyberNewsSource(JsonLdMixin):
    def __init__(self, http_client: HttpClient):
        self._http = http_client

    def discover(self, listing_url: str, language_code: str):
        """Walks /page/{n} pagination — cybernews-specific, nothing outside
        this class knows this shape exists. A fetch failure or an empty
        page (no more links) both just end the generator; producer.py
        treats "stopped early" and "ran out of pages" the same way.
        """
        for page_number in itertools.count(1):
            url = f"{listing_url}/page/{page_number}" if page_number > 1 else listing_url
            try:
                html = self._http.get(url, timeout=REQUEST_TIMEOUT)
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
        html = self._http.get(url, timeout=REQUEST_TIMEOUT)
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
        """(title, author) prefer JSON-LD (see JsonLdMixin) and fall back
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
