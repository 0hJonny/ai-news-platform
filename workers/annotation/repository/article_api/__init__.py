"""Go news API repository. GOLANG_API picks the base URL — same env var
and shape as workers/parser's own repository package.
"""

import os

from .base import ArticleApiRepository
from .golang_api import GolangArticleApiRepository

GOLANG_API = os.environ.get("GOLANG_API", "http://news:5000/api/v1")

article_repository: ArticleApiRepository = GolangArticleApiRepository(GOLANG_API)

__all__ = ["ArticleApiRepository", "GolangArticleApiRepository", "article_repository"]
