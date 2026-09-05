"""Smoke test: build the full Annotate -> Categorize -> ExtractTags ->
Translate pipeline (models/GenerationModels/pipeline.py) against every
GenerationModel subclass with a fake ModelRepository (no real HTTP calls,
no real LLM) and check it runs end to end without raising.

This exists to catch the class of bug that actually broke this once:
repository.model and models.GenerationModels used to import each other,
so whichever module a caller happened to import first decided whether
the app worked at all. That only shows up by actually importing and
exercising both packages together — a plain syntax/lint check doesn't
catch it, and neither does importing just one of them.
"""

from datetime import datetime

import pytest

from models import ArticleAnnotation
from models.GenerationModels import (
    AnnotateStep,
    CategorizeStep,
    ExtractTagsStep,
    Gemma_2b,
    Gemma_4b_e4b,
    Gemma_7b,
    Mistral,
    OpenChat,
    StartPipeline,
    TranslateStep,
)
from repository.model import GenerationResponse

MODEL_CLASSES = [Gemma_2b, Gemma_4b_e4b, Gemma_7b, Mistral, OpenChat]


class FakeModelRepository:
    """Returns just enough content for every operation's own
    prompt-parsing to succeed, keyed off a few keywords in the prompt.
    Good enough to exercise the pipeline structurally — not a claim about
    real model output quality.
    """

    def generate(self, model_name, prompt, stream, options):
        low = prompt.lower()
        if "tags" in low and "translate" not in low:
            content = "[tag1, tag2]"
        elif "classify" in low or "category" in low:
            content = "technology"
        elif "translate" in low:
            content = "Title: Translated Title" if "title" in low else "Translated annotation content"
        else:
            content = "### Main Facts and Events:\n- Fact one"

        return GenerationResponse(
            model=model_name,
            created_at=datetime.now(),
            message={"role": "assistant", "content": content},
            done=True,
            total_duration=0,
            load_duration=0,
            prompt_eval_duration=0,
            eval_count=1,
            eval_duration=0,
        )


@pytest.mark.parametrize("model_cls", MODEL_CLASSES, ids=lambda cls: cls.__name__)
def test_full_pipeline_runs_for_every_model(model_cls):
    model = model_cls(repository=FakeModelRepository())
    article = ArticleAnnotation(id="test-id", title="Test title", body="Test body content.")
    article.language_to_answer_name = "German"

    # Wrapping order is call order, innermost first (see pipeline.py) —
    # TranslateStep has to be outermost since it needs article.annotation
    # already set.
    pipeline = TranslateStep(
        ExtractTagsStep(
            CategorizeStep(
                AnnotateStep(StartPipeline(), model),
                model,
            ),
            model,
        ),
        model,
    )

    result = pipeline.generate(article)

    assert result.annotation
    assert result.theme_name == "technology"
    assert result.tags
    assert result.title
