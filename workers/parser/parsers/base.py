"""Source: the per-source Strategy interface. Each news source (a
config.py SOURCES entry, keyed by its "name") gets its own implementation
of article discovery and content fetching — selected by name via
parsers.get_parser() instead of branching on the source name inline.

Discovery and fetching both live behind this interface, not just parsing —
how a source finds new articles and how it fetches one is itself
source-specific: paginated HTML crawl vs a single RSS/API fetch, /page/{n}
vs /p/{n} vs no pagination at all. producer.py and tasks.py stay fully
agnostic to all of that; they only ever call discover()/fetch_article().
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from bs4 import BeautifulSoup


@dataclass
class DiscoveredArticle:
    url: str
    language_code: str


class Source(Protocol):
    def discover(self, listing_url: str, language_code: str) -> Iterator[DiscoveredArticle]:
        """Lazily yield candidate articles for one configured listing URL.

        Lazy on purpose: a caller that stops iterating early (producer.py
        breaks once it's seen too many already-known links in a row) means
        no further network calls happen — a paginated source never fetches
        a page nobody ended up needing.
        """
        ...

    def fetch_article(self, url: str) -> dict:
        """Return {"title", "author", "body"} for one article URL."""
        ...


class JsonLdMixin:
    """Best-effort (title, author) from schema.org JSON-LD (Article/
    NewsArticle/BlogPosting), which most modern news sites embed for SEO.
    Shared across Source implementations since JSON-LD is a standard, not
    something specific to any one site — far less fragile than scraping
    CSS classes, which drift out from under a redesign (cybernews.com's
    own article-info__link/article-info__date/heading classes already
    have, while its JSON-LD block hasn't). Returns (None, None) on any
    failure/absence so the caller falls back to CSS-based heuristics.
    """

    @staticmethod
    def _parse_json_ld(soup: BeautifulSoup) -> tuple[str | None, str | None]:
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
