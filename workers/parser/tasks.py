"""parsing.scrape_source — the Celery task that fetches and parses
a single article URL (already reserved as a draft row by producer.py), then
hands the result off to the annotation pipeline.

Writes back onto the article via `repository.article_repository`
(repository/base.py) — this module never talks to the Go API directly, it
just calls repository methods and lets that hide the ingest routes,
request building and error handling.

Fetching and parsing the article itself are source-specific and live
behind the Source interface (parsers/base.py) — this task just looks the
right one up via parsers.get_parser(source_name), the same name
producer.py used to discover this article in the first place, and asks it
for the article's content.
"""

import logging

from parsers import get_parser
from repository import article_repository
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
        article_repository.patch_article(article_id, parsing_status=PARSING_ERROR)
        article_repository.log_stage(article_id, STAGE_PARSING, EVENT_FAILED, str(exc))
        return

    article_repository.patch_article(article_id, parsing_status=PARSING_IN_PROGRESS)
    article_repository.log_stage(article_id, STAGE_PARSING, EVENT_STARTED)

    try:
        parsed = source.fetch_article(url)
    except Exception as exc:
        logger.error("[parsing.scrape_source] Failed to fetch/parse %s: %s", url, exc)
        article_repository.patch_article(article_id, parsing_status=PARSING_ERROR)
        article_repository.log_stage(article_id, STAGE_PARSING, EVENT_FAILED, str(exc))
        return

    if not parsed["body"]:
        logger.error("[parsing.scrape_source] Empty body for %s, marking ERROR", url)
        article_repository.patch_article(article_id, parsing_status=PARSING_ERROR)
        article_repository.log_stage(article_id, STAGE_PARSING, EVENT_FAILED, "Parsed page yielded an empty body")
        return

    ok, patch_error = article_repository.patch_article(
        article_id,
        parsing_status=PARSING_DONE,
        title=parsed["title"],
        author=parsed["author"],
        body=parsed["body"],
    )
    if not ok:
        article_repository.patch_article(article_id, parsing_status=PARSING_ERROR)
        article_repository.log_stage(
            article_id, STAGE_PARSING, EVENT_FAILED, patch_error or "Failed to PATCH parsed content back to the Go API"
        )
        return

    article_repository.log_stage(article_id, STAGE_PARSING, EVENT_SUCCEEDED)

    annotation_id, job_error = article_repository.create_annotation_job(article_id)
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
