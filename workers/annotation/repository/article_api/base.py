"""ArticleApiRepository: the interface hiding all HTTP calls to the Go
news API behind — this service's counterpart of
workers/parser/repository/base.py. tasks.py talks to this interface
only; nothing in this service builds a request, knows a route path, or
reads GOLANG_API itself.
"""

from typing import Protocol


class ArticleApiRepository(Protocol):
    def fetch_article(self, article_id: str) -> dict | None:
        """GET /p/articles/:id. Returns the article's data dict, or None
        on any request failure.
        """
        ...

    def patch_annotation(self, annotation_id: str, **fields) -> tuple[bool, str | None]:
        """PATCH /p/annotations/:id — this service's only write path,
        addressing the annotation job row directly by its own id. Returns
        (ok, error_message): the caller needs the real failure reason,
        not just a bool, to log a useful pipeline-stage event.
        """
        ...

    def log_stage(
        self,
        article_id: str,
        stage: str,
        status: str,
        error_message: str | None = None,
        language_id: int | None = None,
    ) -> None:
        """Append a pipeline-stage event (POST /p/articles/:id/events).
        language_id ties the event to the specific annotation job's
        language — None is fine (and expected) when the article couldn't
        even be fetched yet. Best-effort — must never raise, this is an
        observability call, not part of the pipeline's own control flow.
        """
        ...
