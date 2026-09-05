"""ArticleApiRepository: the interface hiding all HTTP calls to the Go
news API's ingest routes (/p/articles/*, see
backend/news/src/routes/routes_private.go) behind. producer.py and
tasks.py talk to this interface only — neither one builds a request,
knows a route path, or reads GOLANG_API itself. Swapping the underlying
HTTP client, or the API itself, means touching this module and its
implementation (golang_api.py), not the task/producer code that calls it.
"""

from typing import Protocol


class ArticleApiRepository(Protocol):
    def create_draft(self, source_link: str, language_code: str) -> tuple[str | None, bool]:
        """Reserve a draft article row for `source_link`. Returns
        (article_id, is_new); is_new is False both on a 409 (some earlier
        run already has this source_link) and on any request failure —
        either way, the caller shouldn't enqueue a fresh scrape for it.
        """
        ...

    def patch_article(self, article_id: str, **fields) -> tuple[bool, str | None]:
        """Write parsed fields onto an existing article. Returns (ok,
        error_message) — the caller needs the real failure reason, not
        just a bool, to log a useful pipeline-stage event.
        """
        ...

    def create_annotation_job(self, article_id: str) -> tuple[str | None, str | None]:
        """Reserve a PENDING annotation job for `article_id` (in the
        article's own language). Returns (annotation_id, error_message);
        a 409 (job already exists, e.g. a retried task) still yields a
        usable annotation_id.
        """
        ...

    def log_stage(self, article_id: str, stage: str, status: str, error_message: str | None = None) -> None:
        """Append a pipeline-stage event. Best-effort — must never raise,
        this is an observability call, not part of the pipeline's own
        control flow.
        """
        ...
