"""LLM backend repository. LLM_PROVIDER picks which one backs every
GenerationModel by default — "ollama" (default, our current backend) or
anything else for an OpenAI-compatible endpoint (llama.cpp server's own
OpenAI API, LM Studio). Same env var and the same two-way split as
news_agent's app/core/llm_provider.py, just choosing this service's HTTP
backend instead of a LangChain chat model.
"""

import os

from .base import ModelRepository
from .GenerationResponse import GenerationResponse
from .ollama_repository import OllamaModelRepository
from .openai_repository import OpenAiModelRepository

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")

# docker-compose reuses OLLAMA_BASE_URL for API_OLLAMA_URL, but that value
# is "/v1"-suffixed for the LangGraph agent's OpenAI-compatible client
# (workers/agent). Both repositories here build their own full path off a
# bare host instead (OllamaModelRepository appends "/api/chat",
# OpenAiModelRepository appends "/v1/chat/completions" itself), so a
# trailing "/v1" would double up into e.g. ".../v1/api/chat" and 404.
# Stripped defensively here rather than requiring a second,
# annotation-only env var.
MODEL_BASE_URL = os.environ.get("API_OLLAMA_URL", "http://localhost:11434").removesuffix("/v1")

model_repository: ModelRepository = (
    OllamaModelRepository(MODEL_BASE_URL)
    if LLM_PROVIDER == "ollama"
    else OpenAiModelRepository(MODEL_BASE_URL)
)

__all__ = [
    "ModelRepository",
    "GenerationResponse",
    "OllamaModelRepository",
    "OpenAiModelRepository",
    "model_repository",
]
