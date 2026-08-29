"""Stage 5: parsing.scrape_source — the Celery task that fetches and parses
a single article URL (already reserved as a draft row by producer.py), then
hands the result off to the annotation pipeline.

Deliberately decoupled from parsers/base_parser.py's BaseParser, which still
does its own JWT login against the old /auth/login + /p/article flow — the
new ingest routes (/p/articles/*, see backend/news/src/routes/routes_private.go)
aren't authenticated, and this task updates a specific article_id the
producer already created instead of creating a brand new row itself.
"""

import json
import logging
import os
import random

import cloudscraper
import requests
from bs4 import BeautifulSoup

from shared.celery_app import app
from shared.statuses import (
    EVENT_FAILED,
    EVENT_STARTED,
    EVENT_SUCCEEDED,
    PARSING_DONE,
    PARSING_ERROR,
    PARSING_IN_PROGRESS,
    STAGE_PARSING,
)

logger = logging.getLogger(__name__)

GOLANG_API = os.environ.get("GOLANG_API", "http://news:5000/api/v1")
REQUEST_TIMEOUT = 15

_PLATFORMS = ["linux", "windows", "darwin", "android"]
_BROWSERS = ["chrome", "firefox"]

# A plain requests.get() 403s on cybernews.com (Cloudflare bot-check) — same
# problem parsers/base_parser.py already solves for this exact site via
# cloudscraper. One scraper per worker process: the Cloudflare-challenge
# solve has real per-instance setup cost, no need to redo it every task.
_scraper = cloudscraper.create_scraper(
    delay=6,
    browser={"browser": random.choice(_BROWSERS), "platform": random.choice(_PLATFORMS)},
)


def _fetch_html(url: str) -> tuple[str | None, str | None]:
    """Returns (html, error_message) — error_message is populated on
    failure so the caller can pass the real reason (not just a generic
    placeholder) into the pipeline-stage log.
    """
    try:
        response = _scraper.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text, None
    except Exception as exc:  # cloudscraper raises beyond plain requests.RequestException
        logger.error("[parsing.scrape_source] Failed to fetch %s: %s", url, exc)
        return None, str(exc)


def _parse_json_ld(soup: BeautifulSoup) -> tuple[str | None, str | None]:
    """Best-effort (title, author) from schema.org JSON-LD (Article/
    NewsArticle/BlogPosting), which most modern news sites embed for SEO.
    Far less fragile than scraping CSS classes — cybernews.com's own
    article-info__link/article-info__date/heading classes (still targeted
    by parsers/cybewnews's site-specific parser) have already drifted out
    from under a redesign, while its JSON-LD block hasn't. Returns
    (None, None) on any failure/absence so the caller falls back to the
    CSS-based heuristics below.
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


def _parse_article(html: str) -> dict:
    """(title, author) prefer JSON-LD (see _parse_json_ld) and fall back to
    CSS-based heuristics only where that came up empty. Body text always
    comes from the CSS side: JSON-LD's NewsArticle node here doesn't carry
    articleBody, only metadata.

    Body is scoped to the nearest <article>/.content container rather than
    the whole page — a page-wide <p> search also picks up header/footer/nav
    boilerplate (copyright notices, menu text) sitting outside the actual
    article, which is exactly what showed up in early test runs. Falls back
    to the whole page if no such container exists, to stay usable on sites
    that don't structure things this way.
    """
    soup = BeautifulSoup(html, "lxml")

    title, author = _parse_json_ld(soup)

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


def _patch_article(article_id: str, **fields) -> tuple[bool, str | None]:
    """PATCH /p/articles/:id/parsed — parsing's only write path onto the
    article row itself. Returns (ok, error_message) — same reasoning as
    _fetch_html: the caller needs the real failure reason, not just a bool,
    to log a useful pipeline-stage event.
    """
    try:
        response = requests.patch(
            f"{GOLANG_API}/p/articles/{article_id}/parsed",
            json={k: v for k, v in fields.items() if v is not None},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True, None
    except requests.RequestException as exc:
        logger.error("[parsing.scrape_source] Failed to PATCH article %s: %s", article_id, exc)
        return False, str(exc)


def _create_annotation_job(article_id: str) -> tuple[str | None, str | None]:
    """POST /p/articles/:id/annotations — reserves a PENDING annotation job
    in the article's own language (no language_code sent). Returns
    (annotation_id, error_message); a 409 (job already exists, e.g. a
    retried task) still yields a usable annotation_id from the response
    body, not an error.
    """
    try:
        response = requests.post(
            f"{GOLANG_API}/p/articles/{article_id}/annotations",
            json={},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code not in (201, 409):
            response.raise_for_status()
        return response.json().get("data", {}).get("id"), None
    except requests.RequestException as exc:
        logger.error("[parsing.scrape_source] Failed to create annotation job for %s: %s", article_id, exc)
        return None, str(exc)


def _log_stage(article_id: str, status: str, error_message: str | None = None) -> None:
    """Appends a PARSING stage event (POST /p/articles/:id/events) —
    separate from _patch_article's PATCH, which only updates the article's
    current summary state. This is what makes "which stage did it actually
    die in, and why" a query instead of a guess from ERROR alone. Errors
    logging the log itself are swallowed (best-effort, must never crash the
    task over an observability call).
    """
    try:
        response = requests.post(
            f"{GOLANG_API}/p/articles/{article_id}/events",
            json={"stage": STAGE_PARSING, "status": status, "error_message": error_message},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("[parsing.scrape_source] Failed to log stage event for %s: %s", article_id, exc)


@app.task(name="parsing.scrape_source")
def scrape_source(article_id: str, url: str):
    """Fetch `url`, parse it, PATCH the result into the Go API
    (parsing_status -> PARSED), reserve an annotation job for the article's
    own language, and enqueue annotation.annotate_article for that job.
    Marks the article ERROR instead of leaving it stuck in PARSING if
    anything fails — annotation's own status is untouched either way, it's
    a separate row now (see models.AnnotationStatus on the Go side).
    """
    logger.info("[parsing.scrape_source] %s -> %s", article_id, url)

    _patch_article(article_id, parsing_status=PARSING_IN_PROGRESS)
    _log_stage(article_id, EVENT_STARTED)

    html, fetch_error = _fetch_html(url)
    if html is None:
        _patch_article(article_id, parsing_status=PARSING_ERROR)
        _log_stage(article_id, EVENT_FAILED, fetch_error or "Fetch failed for an unknown reason")
        return

    parsed = _parse_article(html)
    if not parsed["body"]:
        logger.error("[parsing.scrape_source] Empty body for %s, marking ERROR", url)
        _patch_article(article_id, parsing_status=PARSING_ERROR)
        _log_stage(article_id, EVENT_FAILED, "Parsed page yielded an empty body")
        return

    ok, patch_error = _patch_article(
        article_id,
        parsing_status=PARSING_DONE,
        title=parsed["title"],
        author=parsed["author"],
        body=parsed["body"],
    )
    if not ok:
        _patch_article(article_id, parsing_status=PARSING_ERROR)
        _log_stage(article_id, EVENT_FAILED, patch_error or "Failed to PATCH parsed content back to the Go API")
        return

    _log_stage(article_id, EVENT_SUCCEEDED)

    annotation_id, job_error = _create_annotation_job(article_id)
    if annotation_id is None:
        # Parsing itself succeeded — only the handoff to annotation failed.
        # Don't mark the article ERROR for this; parsing_status=PARSED
        # stands, there's just no annotation job to show for it yet.
        logger.error(
            "[parsing.scrape_source] Could not create/find an annotation job for %s: %s",
            article_id,
            job_error,
        )
        return

    # annotation.annotate_article is defined in a different container
    # (workers/annotation, its own build context/volume — see
    # infra/docker-compose.yml) so it can't be imported here directly.
    # send_task() enqueues by task NAME onto whichever queue task_routes
    # maps it to (annotation_queue, per shared/celery_app.py); the
    # annotation worker consuming that queue resolves the name to its own
    # locally-registered task. Equivalent to calling
    # annotate_article.delay(article_id, annotation_id) if that import were
    # possible.
    app.send_task("annotation.annotate_article", args=[article_id, annotation_id])
    logger.info(
        "[parsing.scrape_source] Enqueued annotation.annotate_article(%s, %s)", article_id, annotation_id
    )
