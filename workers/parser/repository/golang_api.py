"""GolangArticleApiRepository: requests-based implementation of
ArticleApiRepository. This is the only module in workers/parser that
builds a URL or imports `requests` for talking to the Go news API —
producer.py and tasks.py just call repository methods and never see the
transport underneath.
"""

import logging

import requests

logger = logging.getLogger(__name__)


class GolangArticleApiRepository:
    def __init__(self, base_url: str, timeout: float = 15):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def create_draft(self, source_link: str, language_code: str) -> tuple[str | None, bool]:
        try:
            response = requests.post(
                f"{self.base_url}/p/articles",
                json={"source_link": source_link, "language_code": language_code},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to create draft for %s: %s", source_link, exc)
            return None, False

        if response.status_code == 201:
            return response.json().get("data", {}).get("id"), True
        if response.status_code == 409:
            return response.json().get("data", {}).get("id"), False

        logger.error(
            "[GolangArticleApiRepository] Unexpected response creating draft for %s: %s %s",
            source_link,
            response.status_code,
            response.text,
        )
        return None, False

    def patch_article(self, article_id: str, **fields) -> tuple[bool, str | None]:
        try:
            response = requests.patch(
                f"{self.base_url}/p/articles/{article_id}/parsed",
                json={k: v for k, v in fields.items() if v is not None},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True, None
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to PATCH article %s: %s", article_id, exc)
            return False, str(exc)

    def create_annotation_job(self, article_id: str) -> tuple[str | None, str | None]:
        try:
            response = requests.post(
                f"{self.base_url}/p/articles/{article_id}/annotations",
                json={},
                timeout=self.timeout,
            )
            if response.status_code not in (201, 409):
                response.raise_for_status()
            return response.json().get("data", {}).get("id"), None
        except requests.RequestException as exc:
            logger.error(
                "[GolangArticleApiRepository] Failed to create annotation job for %s: %s", article_id, exc
            )
            return None, str(exc)

    def log_stage(self, article_id: str, stage: str, status: str, error_message: str | None = None) -> None:
        try:
            response = requests.post(
                f"{self.base_url}/p/articles/{article_id}/events",
                json={"stage": stage, "status": status, "error_message": error_message},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error("[GolangArticleApiRepository] Failed to log stage event for %s: %s", article_id, exc)
