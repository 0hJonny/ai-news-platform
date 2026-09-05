"""GolangArticleApiRepository: requests-based implementation of
ArticleApiRepository, talking to the same Go news API ingest routes as
workers/parser's own repository (see
backend/news/src/routes/routes_private.go). This is the only module in
workers/annotation that builds a URL or imports `requests` for it —
tasks.py just calls repository methods.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class GolangArticleApiRepository:
    def __init__(self, base_url: str, timeout: float = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def fetch_article(self, article_id: str) -> dict | None:
        try:
            response = requests.get(f"{self.base_url}/p/articles/{article_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json().get("data")
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to fetch article %s: %s", article_id, exc)
            return None

    def patch_annotation(self, annotation_id: str, **fields) -> tuple[bool, str | None]:
        try:
            response = requests.patch(
                f"{self.base_url}/p/annotations/{annotation_id}",
                json={k: v for k, v in fields.items() if v is not None},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to PATCH annotation %s: %s", annotation_id, exc)
            return False, str(exc)

    def log_stage(
        self,
        article_id: str,
        stage: str,
        status: str,
        error_message: str | None = None,
        language_id: int | None = None,
    ) -> None:
        try:
            response = requests.post(
                f"{self.base_url}/p/articles/{article_id}/events",
                json={
                    "stage": stage,
                    "status": status,
                    "error_message": error_message,
                    "language_id": language_id,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to log stage event for %s: %s", article_id, exc)
