"""OpenAiModelRepository: the alternative backend, for anything speaking
the OpenAI-compatible /v1/chat/completions protocol — llama.cpp server's
own OpenAI-compatible API and LM Studio both do. Which repository a
GenerationModel actually gets is decided once, in __init__.py.
"""

import logging
import os

import requests

from .GenerationResponse import GenerationResponse

logger = logging.getLogger(__name__)


class OpenAiModelRepository:
    def __init__(self, base_url: str, api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        # llama.cpp server / LM Studio don't require a key at all; kept
        # optional for a provider that does (an OpenAI-compatible cloud
        # endpoint pointed at the same code path).
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")

    def generate(
        self, model_name: str, prompt: str, stream: bool, options: dict
    ) -> GenerationResponse | None:
        # Unlike Ollama's nested "options", OpenAI-style servers take
        # generation params (temperature, top_p, repeat_penalty, ...)
        # as top-level fields — llama.cpp server and LM Studio both
        # accept the Ollama-shaped option names here too, so options is
        # passed through as-is rather than translated key by key.
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream,
            **(options or {}),
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        try:
            response = requests.post(f"{self.base_url}/v1/chat/completions", json=data, headers=headers)
            if response.status_code == 200:
                return GenerationResponse.from_openai_json(response.json())
            logger.error("[OpenAiModelRepository] Error: %s", response.status_code)
            return None
        except requests.exceptions.RequestException as exc:
            logger.error("[OpenAiModelRepository] Request error: %s", exc)
            return None
