"""Composition root for the Go news API repository. producer.py and
tasks.py import `article_repository` from here instead of building their
own client — same pattern as parsers.get_parser() being the one place
that wires a Source to its HttpClient.
"""

import os

from .base import ArticleApiRepository
from .golang_api import GolangArticleApiRepository

GOLANG_API = os.environ.get("GOLANG_API", "http://news:5000/api/v1")

article_repository: ArticleApiRepository = GolangArticleApiRepository(GOLANG_API)

__all__ = ["ArticleApiRepository", "GolangArticleApiRepository", "article_repository"]
