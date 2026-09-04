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

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


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
