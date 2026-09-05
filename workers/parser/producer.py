"""producer — walks each configured source's listing URLs (config.py's
SOURCES), discovers candidate articles via that source's Source
implementation (parsers/registry.py, selected by the source's `name`), and
for every genuinely new one reserves a draft via `repository.article_repository`
and enqueues parsing.scrape_source to actually fetch+parse it.

How a source finds articles — paginated HTML crawl, RSS fetch, whatever —
lives entirely behind Source.discover() (see parsers/base.py); this module
only handles the generic parts: pulling candidates from that generator,
deduping against the Go API (via the repository, never directly), deciding
when a source has run dry, and enqueueing Celery tasks. It has no idea what
a "page" is, and doesn't fetch any HTML itself.

Run manually, or via the parser-producer service's cron
(infra/docker-compose.yml, workers/parser/cronjob):
    python producer.py
"""

import logging

from config import SOURCES
from parsers import Source, get_parser
from repository import article_repository
from tasks import scrape_source

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mirrors the old CyberNewsProducer's max_duplicates early-stop: once this
# many discovered links in a row turn out to already exist, assume this run
# has caught up with whatever a previous run already ingested and stop
# pulling more out of source.discover(). For a paginated source that's what
# keeps a run from re-walking hundreds of old pages every 12 hours; for a
# source with no pagination at all it just never triggers.
MAX_DUPLICATE_STREAK = 13


def _walk_listing(listing_url: str, language_code: str, source_name: str, source: Source) -> tuple[int, int]:
    """Pulls candidate articles from `source.discover()` one at a time,
    creates a draft for each via the repository, and enqueues
    parsing.scrape_source for the ones that are genuinely new. Stops after
    MAX_DUPLICATE_STREAK consecutive already-known links by simply
    `break`-ing this loop — since discover() is a lazy generator, breaking
    just stops pulling from it, so whatever fetching it would've done for
    further results (e.g. the next HTML page) never happens.
    """
    new_count = 0
    enqueued_count = 0
    duplicate_streak = 0

    for article in source.discover(listing_url, language_code):
        article_id, is_new = article_repository.create_draft(article.url, language_code)
        if not article_id or not is_new:
            duplicate_streak += 1
            if duplicate_streak >= MAX_DUPLICATE_STREAK:
                logger.info(
                    "[producer] %s: hit %d consecutive already-known links, stopping",
                    listing_url,
                    MAX_DUPLICATE_STREAK,
                )
                break
            continue

        duplicate_streak = 0
        new_count += 1
        scrape_source.delay(article_id, article.url, source_name)
        enqueued_count += 1
        logger.info("[producer] Enqueued parsing.scrape_source(%s, %s)", article_id, article.url)

    return new_count, enqueued_count


def run():
    total_new = 0
    total_enqueued = 0

    for source_cfg in SOURCES:
        source = get_parser(source_cfg["name"])
        language_code = source_cfg["language_code"]
        for listing_url in source_cfg["urls"]:
            new_count, enqueued_count = _walk_listing(listing_url, language_code, source_cfg["name"], source)
            total_new += new_count
            total_enqueued += enqueued_count

    logger.info("[producer] Done: %d new article(s), %d enqueued", total_new, total_enqueued)


if __name__ == "__main__":
    run()
