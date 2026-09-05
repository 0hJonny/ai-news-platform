"""Re-exports every pluggable LLM backend plus the shared
GenerationModel interface they all implement — only Gemma_4b_e4b is
actually wired into tasks.py today, the rest are alternatives available to
swap in, not dead code, hence the explicit `as` re-exports below rather
than removing the "unused" ones.

Also re-exports pipeline.py's decorator steps (AnnotateStep,
CategorizeStep, ExtractTagsStep, TranslateStep, and StartPipeline to
start a chain) — how a caller composes a model's operations into an
ordered pipeline, see pipeline.py's own docstring.
"""

from .Gemma_2b import Gemma_2b as Gemma_2b
from .Gemma_4b_e4b import Gemma_4b_e4b as Gemma_4b_e4b
from .Gemma_7b import Gemma_7b as Gemma_7b
from .GenerationModel import GenerationModel as GenerationModel
from .Mistral import Mistral as Mistral
from .OpenChat import OpenChat as OpenChat
from .pipeline import AnnotateStep as AnnotateStep
from .pipeline import ArticleGenerator as ArticleGenerator
from .pipeline import CategorizeStep as CategorizeStep
from .pipeline import ExtractTagsStep as ExtractTagsStep
from .pipeline import StartPipeline as StartPipeline
from .pipeline import TranslateStep as TranslateStep
