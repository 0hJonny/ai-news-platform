"""parsing.scrape_source — the Celery task that fetches and parses
a single article URL (already reserved as a draft row by producer.py), then
hands the result off to the annotation pipeline.

Talks to the new unauthenticated ingest routes (/p/articles/*, see
backend/news/src/routes/routes_private.go) and updates a specific
article_id the producer already created, instead of creating a brand new
row itself.

Fetching and parsing the article itself are source-specific and live
behind the Source interface (parsers/base.py) — this task just looks the
right one up via parsers.get_parser(source_name), the same name
producer.py used to discover this article in the first place, and asks it
for the article's content.
"""

import logging
import os

import requests

from parsers import get_parser
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


def _patch_article(article_id: str, **fields) -> tuple[bool, str | None]:
    """PATCH /p/articles/:id/parsed — parsing's only write path onto the
    article row itself. Returns (ok, error_message) — the caller needs the
    real failure reason, not just a bool, to log a useful pipeline-stage
    event.
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
def scrape_source(article_id: str, url: str, source_name: str):
    """Fetch+parse `url` via the Source registered for `source_name`
    (parsers/registry.py — the same name producer.py used to discover this
    article), PATCH the result into the Go API (parsing_status -> PARSED),
    reserve an annotation job for the article's own language, and enqueue
    annotation.annotate_article for that job. Marks the article ERROR
    instead of leaving it stuck in PARSING if anything fails — annotation's
    own status is untouched either way, it's a separate row now (see
    models.AnnotationStatus on the Go side).
    """
    logger.info("[parsing.scrape_source] %s -> %s (source=%s)", article_id, url, source_name)

    try:
        source = get_parser(source_name)
    except ValueError as exc:
        logger.error("[parsing.scrape_source] %s", exc)
        _patch_article(article_id, parsing_status=PARSING_ERROR)
        _log_stage(article_id, EVENT_FAILED, str(exc))
        return

    _patch_article(article_id, parsing_status=PARSING_IN_PROGRESS)
    _log_stage(article_id, EVENT_STARTED)

    try:
        parsed = source.fetch_article(url)
    except Exception as exc:
        logger.error("[parsing.scrape_source] Failed to fetch/parse %s: %s", url, exc)
        _patch_article(article_id, parsing_status=PARSING_ERROR)
        _log_stage(article_id, EVENT_FAILED, str(exc))
        return

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
        _log_stage(
            article_id, EVENT_FAILED, patch_error or "Failed to PATCH parsed content back to the Go API"
        )
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
