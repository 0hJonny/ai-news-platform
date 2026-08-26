import requests
from .GenerationResponse import GenerationResponse
from models import ArticleAnnotation

class GenerationModel:
    def __init__(self):
        self.model_name = "GenerationModel"
        self.api_url = ""
        self.data = {
            "stream": False,  # Placeholder for stream option
            "options": {
                "temperature": 0.8,  # Placeholder for temperature option
                "repeat_penalty": 1.0  # Placeholder for repeat_penalty option
            }
        }

    def set_api_url(self, api_url: str):
        if self.api_url != api_url:
            self.api_url = api_url

    def __str__(self):
        return self.model_name
    
    def annotate(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(f"Метод generate_text должен быть реализован в подклассе вашей модели, {self.model_name}.")
    
    def translate(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(f"Метод translate должен быть реализован в подклассе вашей модели, {self.model_name}.")

    def categorize(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(f"Метод categorize должен быть реализован в подклассе вашей модели, {self.model_name}.")
    
    def extract_tags(self, article: ArticleAnnotation, stream=False, options=None) -> ArticleAnnotation:
        raise NotImplementedError(f"Метод extract_tags должен быть реализован в подклассе вашей модели, {self.model_name}.")
    
    def _generate_text(self, prompt: str, stream=None, options=None) -> GenerationResponse:
        if stream is None:
            stream = self.data["stream"]
        if options is None:
            options = self.data["options"]


        data = {
            "model": self.model_name,
            "messages": [
                { "role": "user", "content": prompt }
            ],
            "stream": stream,
            "options": options
        }
        try:
            response = requests.post(f"{self.api_url}/api/chat", json=data)
            if response.status_code == 200:
                return GenerationResponse.from_json(response.json())
            else:
                print(f"Error: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None