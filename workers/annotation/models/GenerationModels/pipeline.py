"""Decorator-pattern pipeline over GenerationModel's per-operation methods
(annotate/categorize/extract_tags/translate) — this replaces a call site
hardcoding "call annotate, then translate, then ..." with composing an
object graph of steps once and calling .generate() on the outermost one.

Each step wraps the previous step (`component`) and runs it first, then
applies its own model call on the result — so wrapping order IS call
order, innermost first. That matters here: TranslateStep needs
article.annotation already set (see GenerationModel subclasses'
translate() — they raise if it's None), so it always has to be the
outermost wrap, e.g. for an article that needs a translated, categorized,
tagged annotation:

    model = Gemma_4b_e4b()
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
    article = pipeline.generate(article)

Adding a new operation later (anything else GenerationModel-shaped) means
adding one more small *Step subclass here — nothing in
models/GenerationModels/*.py's prompt-building/parsing, or in whatever
calls the pipeline, has to change.
"""

from typing import Protocol

from models import ArticleAnnotation

from .GenerationModel import GenerationModel


class ArticleGenerator(Protocol):
    def generate(self, article: ArticleAnnotation) -> ArticleAnnotation:
        """Return `article` transformed by this step (and, for a
        decorator, everything it wraps)."""
        ...


class StartPipeline:
    """The identity step every chain starts from — returns the article
    unchanged, so the innermost real step has something to wrap.
    """

    def generate(self, article: ArticleAnnotation) -> ArticleAnnotation:
        return article


class GenerationStep:
    """Base decorator: run `component` first, then this step's own model
    call on the result it produced. Concrete steps below only need to say
    which GenerationModel method they call.
    """

    def __init__(self, component: ArticleGenerator, model: GenerationModel):
        self.component = component
        self.model = model

    def _apply(self, article: ArticleAnnotation) -> ArticleAnnotation:
        raise NotImplementedError

    def generate(self, article: ArticleAnnotation) -> ArticleAnnotation:
        article = self.component.generate(article)
        return self._apply(article)


class AnnotateStep(GenerationStep):
    def _apply(self, article: ArticleAnnotation) -> ArticleAnnotation:
        return self.model.annotate(article)


class CategorizeStep(GenerationStep):
    def _apply(self, article: ArticleAnnotation) -> ArticleAnnotation:
        return self.model.categorize(article)


class ExtractTagsStep(GenerationStep):
    def _apply(self, article: ArticleAnnotation) -> ArticleAnnotation:
        return self.model.extract_tags(article)


class TranslateStep(GenerationStep):
    def _apply(self, article: ArticleAnnotation) -> ArticleAnnotation:
        return self.model.translate(article)
