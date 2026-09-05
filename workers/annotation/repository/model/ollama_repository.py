"""OllamaModelRepository: our current backend, talking to Ollama's native
/api/chat endpoint — exactly the request GenerationModel._generate_text
used to build itself, just moved here behind ModelRepository.
"""

import logging

import requests

from .GenerationResponse import GenerationResponse

logger = logging.getLogger(__name__)


class OllamaModelRepository:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(
        self, model_name: str, prompt: str, stream: bool, options: dict
    ) -> GenerationResponse | None:
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            "options": options,
        }
        try:
            response = requests.post(f"{self.base_url}/api/chat", json=data)
            if response.status_code == 200:
                return GenerationResponse.from_json(response.json())
            logger.error("[OllamaModelRepository] Error: %s", response.status_code)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("[OllamaModelRepository] Request error: %s", exc)
            return None
