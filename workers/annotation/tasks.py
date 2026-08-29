"""Stage 5: annotation.annotate_article — the Celery task that fetches a
parsed article from the Go API, runs it through the existing Ollama-based
annotation pipeline, and PATCHes the result back onto its own annotation
job row (PATCH /p/annotations/:id) with status ANNOTATED.

The job row (news.annotations, one per (article, language)) is created by
parsing.scrape_source via POST /p/articles/:id/annotations once parsing
succeeds — this task only ever updates it by id, never touches the
article's own parsing_status. That split is what lets annotation stay
independent of parsing's state and, eventually, run more than once per
article (multi-language) with no further schema/API change.

The LLM call itself reuses the pre-existing pipeline as-is
(services/ArticleService.py + models/GenerationModels/Gemma_4b_e4b.py) —
same model.annotate() call the old main.py made via its QueueManager pull
loop, just fed from the new Go-API payload instead. translate/categorize/
extract_tags (the old multi-language + tagging flow) are left out of scope
for this stage; annotate() alone is what's needed to reach ANNOTATED.
"""

import logging
import os

import requests

from shared.celery_app import app
from shared.statuses import (
    ANNOTATION_DONE,
    ANNOTATION_ERROR,
    EVENT_FAILED,
    EVENT_STARTED,
    EVENT_SUCCEEDED,
    STAGE_ANNOTATION,
)
from models import ArticleAnnotation
from services import ArticleService
from models.GenerationModels import Gemma_4b_e4b

logger = logging.getLogger(__name__)

GOLANG_API = os.environ.get("GOLANG_API", "http://news:5000/api/v1")
REQUEST_TIMEOUT = 30


def _fetch_article(article_id: str) -> dict | None:
    try:
        response = requests.get(f"{GOLANG_API}/p/articles/{article_id}", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json().get("data")
    except requests.RequestException as exc:
        logger.error("[annotation.annotate_article] Failed to fetch article %s: %s", article_id, exc)
        return None


def _patch_annotation(annotation_id: str, **fields) -> tuple[bool, str | None]:
    """PATCH /p/annotations/:id — this task's only write path, addressing
    the job row directly by its own id. Returns (ok, error_message): the
    real failure reason, not just a bool, so callers can log a useful
    pipeline-stage event on failure.
    """
    try:
        response = requests.patch(
            f"{GOLANG_API}/p/annotations/{annotation_id}",
            json={k: v for k, v in fields.items() if v is not None},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return True, None
    except requests.RequestException as exc:
        logger.error("[annotation.annotate_article] Failed to PATCH annotation %s: %s", annotation_id, exc)
        return False, str(exc)


def _log_stage(
    article_id: str, status: str, error_message: str | None = None, language_id: int | None = None
) -> None:
    """Appends an ANNOTATION stage event (POST /p/articles/:id/events) —
    separate from _patch_annotation's PATCH, which only updates the job's
    current state. Lets a query answer "which stage did this article
    actually die in, and why" instead of just ERROR with no context.
    language_id ties the event to the specific annotation job's language
    (see article_pipeline_log.language_id) — nil is fine (and expected)
    when the article couldn't even be fetched yet. Best-effort: a failure
    logging the log itself must never crash the task.
    """
    try:
        response = requests.post(
            f"{GOLANG_API}/p/articles/{article_id}/events",
            json={
                "stage": STAGE_ANNOTATION,
                "status": status,
                "error_message": error_message,
                "language_id": language_id,
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("[annotation.annotate_article] Failed to log stage event for %s: %s", article_id, exc)


@app.task(name="annotation.annotate_article")
def annotate_article(article_id: str, annotation_id: str):
    logger.info("[annotation.annotate_article] %s (job %s)", article_id, annotation_id)

    data = _fetch_article(article_id)
    language_id = data.get("language_id") if data else None
    _log_stage(article_id, EVENT_STARTED, language_id=language_id)

    if data is None:
        _patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        _log_stage(article_id, EVENT_FAILED, "Failed to fetch the article from the Go API", language_id=language_id)
        return

    if not data.get("body"):
        logger.error("[annotation.annotate_article] Article %s has no body yet", article_id)
        _patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        _log_stage(
            article_id,
            EVENT_FAILED,
            "Article has no body yet (parsing hasn't produced one)",
            language_id=language_id,
        )
        return

    article = ArticleAnnotation(
        id=article_id,
        title=data.get("title") or "",
        body=data["body"],
    )

    try:
        article = ArticleService.annotate(article, model=Gemma_4b_e4b())
    except Exception as exc:  # LLM call: kept broad on purpose, any failure -> ERROR
        logger.error("[annotation.annotate_article] LLM annotation failed for %s: %s", article_id, exc)
        _patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        _log_stage(article_id, EVENT_FAILED, str(exc), language_id=language_id)
        return

    if not article.annotation:
        logger.error("[annotation.annotate_article] Model returned no annotation for %s", article_id)
        _patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        _log_stage(article_id, EVENT_FAILED, "Model returned an empty annotation", language_id=language_id)
        return

    ok, patch_error = _patch_annotation(
        annotation_id,
        status=ANNOTATION_DONE,
        annotation=article.annotation,
        neural_network=article.neural_networks.get("annotator"),
    )
    if not ok:
        _patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        _log_stage(
            article_id,
            EVENT_FAILED,
            patch_error or "Failed to PATCH the annotation back to the Go API",
            language_id=language_id,
        )
        return

    _log_stage(article_id, EVENT_SUCCEEDED, language_id=language_id)
