import os

from models.GenerationModels import GenerationModel
from models import ArticleAnnotation


class ArticleService:
    # docker-compose reuses OLLAMA_BASE_URL for API_OLLAMA_URL, but that
    # value is "/v1"-suffixed for the LangGraph agent's OpenAI-compatible
    # client (workers/agent) — GenerationModel._generate_text posts to
    # Ollama's native "{api_url}/api/chat" instead, so a trailing "/v1"
    # would double up into ".../v1/api/chat" and 404. Strip it defensively
    # rather than requiring a second, annotation-only env var.
    api_ollama_url: str = os.getenv("API_OLLAMA_URL", "http://localhost:11434").removesuffix("/v1")

    @classmethod
    def _set_api_url(cls, model: GenerationModel) -> None:
        """Set the API URL for a GenerationModel instance."""
        model.set_api_url(cls.api_ollama_url)

    @classmethod
    def annotate(cls, article: ArticleAnnotation, model: GenerationModel = GenerationModel) -> ArticleAnnotation:
        """Annotate an article using a GenerationModel instance."""
        cls._set_api_url(model)
        return model.annotate(article)

    @classmethod
    def translate(cls, article: ArticleAnnotation, model: GenerationModel = GenerationModel) -> ArticleAnnotation:
        """Translate an article using a GenerationModel instance."""
        cls._set_api_url(model)
        return model.translate(article)

    @classmethod
    def extract_tags(cls, article: ArticleAnnotation, model: GenerationModel = GenerationModel) -> ArticleAnnotation:
        """Extract tags from an article using a GenerationModel instance."""
        cls._set_api_url(model)
        return model.extract_tags(article)

    @classmethod
    def categorize(cls, article: ArticleAnnotation, model: GenerationModel = GenerationModel) -> ArticleAnnotation:
        """Categorize an article using a GenerationModel instance."""
        cls._set_api_url(model)
        return model.categorize(article=article)


