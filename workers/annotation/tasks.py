"""annotation.annotate_article — the Celery task that fetches a
parsed article from the Go API, runs it through the existing Ollama-based
annotation pipeline, and PATCHes the result back onto its own annotation
job row (PATCH /p/annotations/:id) with status ANNOTATED.

The job row (news.annotations, one per (article, language)) is created by
parsing.scrape_source via POST /p/articles/:id/annotations once parsing
succeeds — this task only ever updates it by id, never touches the
article's own parsing_status. That split is what lets annotation stay
independent of parsing's state and, eventually, run more than once per
article (multi-language) with no further schema/API change.

All Go API access goes through `repository.article_repository`
(repository/article_api/golang_api.py) — this module never builds a
request itself. There's no separate service layer either: the one call
sequence (run the model, patch the result) is short enough to live right
here, by the same reasoning as workers/parser/tasks.py.

The LLM call itself reuses the pre-existing pipeline as-is
(models/GenerationModels/Gemma_4b_e4b.py, talking to
`repository.model_repository` underneath, which owns its own base_url —
see repository/model/__init__.py), just composed through
models.GenerationModels.pipeline's decorator steps instead of calling
model.annotate() directly — same model.annotate() call the old main.py
made via its QueueManager pull loop, just fed from the new Go-API payload
instead. translate/categorize/extract_tags (the old multi-language +
tagging flow) are left out of the pipeline for this stage; AnnotateStep
alone is what's needed to reach ANNOTATED — adding e.g. a translated
language means wrapping the pipeline in CategorizeStep/ExtractTagsStep/
TranslateStep too (see pipeline.py's docstring), not changing this task.
"""

import logging

from models import ArticleAnnotation
from models.GenerationModels import AnnotateStep, Gemma_4b_e4b, StartPipeline
from repository import article_repository
from shared.celery_app import app
from shared.statuses import (
    ANNOTATION_DONE,
    ANNOTATION_ERROR,
    EVENT_FAILED,
    EVENT_STARTED,
    EVENT_SUCCEEDED,
    STAGE_ANNOTATION,
)

logger = logging.getLogger(__name__)


@app.task(name="annotation.annotate_article")
def annotate_article(article_id: str, annotation_id: str):
    logger.info("[annotation.annotate_article] %s (job %s)", article_id, annotation_id)

    data = article_repository.fetch_article(article_id)
    language_id = data.get("language_id") if data else None
    article_repository.log_stage(article_id, STAGE_ANNOTATION, EVENT_STARTED, language_id=language_id)

    if data is None:
        article_repository.patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        article_repository.log_stage(
            article_id,
            STAGE_ANNOTATION,
            EVENT_FAILED,
            "Failed to fetch the article from the Go API",
            language_id=language_id,
        )
        return

    if not data.get("body"):
        logger.error("[annotation.annotate_article] Article %s has no body yet", article_id)
        article_repository.patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        article_repository.log_stage(
            article_id,
            STAGE_ANNOTATION,
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

    pipeline = AnnotateStep(StartPipeline(), Gemma_4b_e4b())

    try:
        article = pipeline.generate(article)
    except Exception as exc:  # LLM call: kept broad on purpose, any failure -> ERROR
        logger.error("[annotation.annotate_article] LLM annotation failed for %s: %s", article_id, exc)
        article_repository.patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        article_repository.log_stage(
            article_id, STAGE_ANNOTATION, EVENT_FAILED, str(exc), language_id=language_id
        )
        return

    if not article.annotation:
        logger.error("[annotation.annotate_article] Model returned no annotation for %s", article_id)
        article_repository.patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        article_repository.log_stage(
            article_id,
            STAGE_ANNOTATION,
            EVENT_FAILED,
            "Model returned an empty annotation",
            language_id=language_id,
        )
        return

    ok, patch_error = article_repository.patch_annotation(
        annotation_id,
        status=ANNOTATION_DONE,
        annotation=article.annotation,
        neural_network=article.neural_networks.get("annotator"),
    )
    if not ok:
        article_repository.patch_annotation(annotation_id, status=ANNOTATION_ERROR)
        article_repository.log_stage(
            article_id,
            STAGE_ANNOTATION,
            EVENT_FAILED,
            patch_error or "Failed to PATCH the annotation back to the Go API",
            language_id=language_id,
        )
        return

    article_repository.log_stage(article_id, STAGE_ANNOTATION, EVENT_SUCCEEDED, language_id=language_id)
