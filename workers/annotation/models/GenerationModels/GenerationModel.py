from models import ArticleAnnotation
from repository import GenerationResponse, ModelRepository, model_repository


class GenerationModel:
    def __init__(self, repository: ModelRepository = model_repository):
        self.model_name = "GenerationModel"
        self.repository = repository
        self.data = {
            "stream": False,  # Placeholder for stream option
            "options": {
                "temperature": 0.8,  # Placeholder for temperature option
                "repeat_penalty": 1.0,  # Placeholder for repeat_penalty option
            },
        }

    def __str__(self):
        return self.model_name

    def annotate(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(
            f"Метод generate_text должен быть реализован в подклассе вашей модели, {self.model_name}."
        )

    def translate(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(
            f"Метод translate должен быть реализован в подклассе вашей модели, {self.model_name}."
        )

    def categorize(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(
            f"Метод categorize должен быть реализован в подклассе вашей модели, {self.model_name}."
        )

    def extract_tags(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(
            f"Метод extract_tags должен быть реализован в подклассе вашей модели, {self.model_name}."
        )

    def _generate_text(self, prompt: str, stream=None, options=None) -> GenerationResponse:
        if stream is None:
            stream = self.data["stream"]
        if options is None:
            options = self.data["options"]

        return self.repository.generate(
            model_name=self.model_name,
            prompt=prompt,
            stream=stream,
            options=options,
        )
