"""ModelRepository: the interface hiding how GenerationModel talks HTTP
to whichever LLM server actually backs it. models/GenerationModels/*.py
subclasses (Gemma_2b, Mistral, ...) only ever build prompts and read
`.message["content"]` back off a GenerationResponse — none of them, nor
GenerationModel itself, needs to know which wire protocol is in use
underneath. See ollama_repository.py (our current backend) and
openai_repository.py (llama.cpp server / LM Studio) for the two
implementations, and __init__.py for how one gets picked.

GenerationResponse lives in this package (not under
models/GenerationModels) specifically to keep the dependency
one-directional: models.GenerationModels imports from repository.model,
never the other way around — the reverse import used to exist and made
this pair of packages import-order-dependent (it broke whenever
something imported `repository` before `models.GenerationModels` got a
chance to run first).
"""

from typing import Protocol

from .GenerationResponse import GenerationResponse


class ModelRepository(Protocol):
    def generate(
        self, model_name: str, prompt: str, stream: bool, options: dict
    ) -> GenerationResponse | None:
        """Send one chat request for `model_name` against this
        repository's own base_url and return a normalized
        GenerationResponse, or None on failure/a non-200 response — the
        same contract GenerationModel._generate_text always had, just
        moved behind this interface so the transport (and its base_url)
        can be swapped.
        """
        ...
