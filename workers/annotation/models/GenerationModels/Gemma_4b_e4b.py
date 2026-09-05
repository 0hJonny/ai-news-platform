import re

from models import ArticleAnnotation
from repository import GenerationResponse, ModelRepository, model_repository

from .GenerationModel import GenerationModel


class Gemma_4b_e4b(GenerationModel):
    def __init__(self, repository: ModelRepository = model_repository):
        super().__init__(repository)
        self.model_name = "gemma4:e4b"
        self.data = {
            "stream": False,
            "options": {"temperature": 0.1, "top_p": 0.9, "top_k": 40, "repeat_penalty": 1.1},
        }

    def annotate(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        # For Gemma, it's better to give the role and instruction first, then the template, then the data.
        prompt = """You are an expert text analyst. Read the article below and generate an annotation strictly using the provided Markdown template. 
Do not add any greetings or concluding remarks.

TEMPLATE:
### Main Facts and Events:
- [List the main facts and events]

### Key Ideas:
- [Summarize the key ideas or arguments]

### Further Interest:
- [Highlight information that sparks interest]

### Important Keywords:
- *Keywords*: [List important keywords]

### Highlighted Text:
- [Insert highlighted quotes from the article]

ARTICLE TITLE: {title}
ARTICLE CONTENT: {body}

OUTPUT EXACTLY FOLLOWING THE TEMPLATE:"""

        # Recommend using .format(), it's more modern and safer than %s
        prompt = prompt.format(title=article.title, body=article.body)

        answer: GenerationResponse = self._generate_text(prompt=prompt, stream=stream, options=options)
        content = answer.message["content"]

        index = content.find("###")
        if index != -1:
            content = content[index:]

        article.annotation = content
        article.add_neural_network("annotator", self.model_name)

        return article

    def translate(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        # Fixed 'Safe the structure' to 'Preserve the original formatting'
        prompt_title = """Translate the following article title to {lang}. Return ONLY the translated text, nothing else.
        
Title: {title}"""
        prompt_title = prompt_title.format(lang=article.language_to_answer_name, title=article.title)

        answer_title = self._generate_text(prompt=prompt_title, stream=stream, options=options)
        article.title = answer_title.message["content"].strip(" \"'")

        if article.annotation is None:
            raise Exception("Annotation is None. Write annotation before translating.")

        prompt_annotation = """Translate the following article annotation to {lang}. 
Crucially, preserve all Markdown formatting (### Headers, - bullet points, *italics*). Do not add any introductory text.

Annotation:
{annotation}"""
        prompt_annotation = prompt_annotation.format(
            lang=article.language_to_answer_name, annotation=article.annotation
        )

        answer_ann = self._generate_text(prompt=prompt_annotation, stream=stream, options=options)
        article.annotation = answer_ann.message["content"]

        article.add_neural_network("translator", self.model_name)

        return article

    def categorize(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        # Gemma often responds with: "The category is: technology."
        # So we strictly constrain its answer in the prompt.
        prompt = """Analyze the article below and classify it into EXACTLY ONE of the following categories:
- technology
- crypto
- privacy
- security

Return ONLY the category name. Do not explain your choice. Do not use punctuation.

Title: {title}
Content: {body}

Category:"""
        prompt = prompt.format(title=article.title, body=article.body)
        answer = self._generate_text(prompt=prompt, stream=stream, options=options)

        words = ["technology", "crypto", "privacy", "security"]
        content = answer.message["content"].lower()

        article.theme_name = None
        for word in words:
            if word in content:
                article.theme_name = word
                break

        return article

    def extract_tags(self, article: ArticleAnnotation, stream=None, options=None) -> ArticleAnnotation:
        # To avoid parsing complex text, we force the model to output a JSON-like array format
        prompt = """Extract concise tags that represent the main points of the article.
Each tag should be 1-2 words.
Format your answer STRICTLY as a comma-separated list inside square brackets. 
Example: [AI, blockchain, data privacy]
Do not add any other text.

Title: {title}
Content: {body}

Tags:"""
        prompt = prompt.format(title=article.title, body=article.body)

        answer: GenerationResponse = self._generate_text(prompt=prompt, stream=stream, options=options)
        content = answer.message["content"]
        print("Raw Gemma Answer:", content)

        # A more reliable way to extract the data in brackets using a regular expression
        # If the model answers "Here are your tags: [tech, crypto]", we'll only take [tech, crypto]
        match = re.search(r"\[(.*?)\]", content)
        if match:
            tags_str = match.group(1)
            # Split by comma and strip extra whitespace around each tag
            tags_list = [tag.strip(" \"'") for tag in tags_str.split(",") if tag.strip()]

            # In Python, list comprehensions `[foo() for bar in baz]` aren't meant to be used
            # just to call a function (for side effects). A plain for loop reads better.
            for tag in tags_list:
                article.add_tag(tag)

        return article
