from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class GenerationResponse:
    model: str
    created_at: datetime
    message: dict[str, Any]
    done: bool
    total_duration: int
    load_duration: int
    prompt_eval_duration: int
    eval_count: int
    eval_duration: int

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "GenerationResponse":
        """
        A constructor method that creates an instance of the class from a dictionary.

        Parameters:
            data (dict): A dictionary containing the necessary data to create the instance.

        Returns:
            An instance of the class initialized with the data from the dictionary.
        """
        return cls(
            model=data["model"],
            created_at=datetime.fromisoformat(data["created_at"][:26]),
            message=data["message"],
            done=data["done"],
            total_duration=data["total_duration"],
            load_duration=data["load_duration"],
            prompt_eval_duration=data["prompt_eval_duration"],
            eval_count=data.get("eval_count", 1),
            eval_duration=data["eval_duration"],
        )

    @classmethod
    def from_openai_json(cls, data: dict[str, Any]) -> "GenerationResponse":
        """Same normalized shape as from_json, but for an OpenAI-compatible
        /v1/chat/completions response (llama.cpp server, LM Studio) —
        callers only ever read `.message["content"]` off either, so the
        Ollama-only timing fields (total_duration, load_duration, ...) are
        filled with harmless zeros here rather than left to break callers
        that don't need them.
        """
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return cls(
            model=data.get("model", ""),
            created_at=datetime.fromtimestamp(data["created"]) if "created" in data else datetime.now(),
            message=choice["message"],
            done=choice.get("finish_reason") is not None,
            total_duration=0,
            load_duration=0,
            prompt_eval_duration=0,
            eval_count=usage.get("completion_tokens", 1),
            eval_duration=0,
        )
