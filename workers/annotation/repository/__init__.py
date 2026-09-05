"""Composition root aggregating this service's two independent
repositories, each in its own subpackage so they don't get tangled
together:

- .model — model_repository (ModelRepository): the LLM backend a
  GenerationModel talks to (Ollama or an OpenAI-compatible server).
- .article_api — article_repository (ArticleApiRepository): the Go news
  API's ingest routes.

tasks.py and models/GenerationModels/*.py import the singletons re-exported
below instead of reaching into either subpackage directly.
"""

from .article_api import ArticleApiRepository, GolangArticleApiRepository, article_repository
from .model import (
    GenerationResponse,
    ModelRepository,
    OllamaModelRepository,
    OpenAiModelRepository,
    model_repository,
)

__all__ = [
    "ModelRepository",
    "GenerationResponse",
    "OllamaModelRepository",
    "OpenAiModelRepository",
    "model_repository",
    "ArticleApiRepository",
    "GolangArticleApiRepository",
    "article_repository",
]
