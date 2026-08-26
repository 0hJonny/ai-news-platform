import os

from models.GenerationModels import GenerationModel
from models import ArticleAnnotation


class ArticleService:
    # api_ollama_url: str = os.getenv("API_OLLAMA_URL")
    api_ollama_url: str = "https://stammer-unworn-glider.ngrok-free.dev"

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


