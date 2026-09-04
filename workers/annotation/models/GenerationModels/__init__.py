"""Re-exports every pluggable LLM backend plus the shared
GenerationModel interface they all implement — only Gemma_4b_e4b is
actually wired into tasks.py today, the rest are alternatives available to
swap in, not dead code, hence the explicit `as` re-exports below rather
than removing the "unused" ones.
"""

from .Gemma_2b import Gemma_2b as Gemma_2b
from .Gemma_4b_e4b import Gemma_4b_e4b as Gemma_4b_e4b
from .Gemma_7b import Gemma_7b as Gemma_7b
from .GenerationModel import GenerationModel as GenerationModel
from .Mistral import Mistral as Mistral
from .OpenChat import OpenChat as OpenChat
