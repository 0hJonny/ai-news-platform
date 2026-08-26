from dataclasses import dataclass, field

@dataclass
class ArticleAnnotation:
    id: str
    title: str
    body: str
    language_code: str = ""
    language_to_answer_code: str = ""
    language_to_answer_name: str = ""
    theme_name: str = ""
    tags: list[str] = field(default_factory=list)
    annotation: str = None
    neural_networks: dict[str, str] = field(default_factory=dict)
    has_annotation: bool = False
    title_orig: str = None

    def check_article_annotation_error(self):
        """Check if the article annotation is valid."""
        if self.title == self.title_orig and self.language_to_answer_code != self.language_code or self.title == "":
            return "Title is None"
        if self.body is None:
            return "Body is None"
        if self.language_code is None:
            return "Language code is None"
        if self.language_to_answer_code is None:
            return "Language to answer code is None"
        if self.language_to_answer_name is None:
            return "Language to answer name is None"
        if self.theme_name is None and not self.has_annotation:
            return "Theme name is None"
        if (self.tags is None or self.tags == ['']) and not self.has_annotation:
            return "Tags is None"
        if self.annotation is None:
            return "Annotation is None"
        if self.neural_networks is None:
            return "Neural networks is None"
        return None


    def add_tag(self, tag: str):
        """Add a tag to the article."""
        if len(tag) <= 20 and not self.tags:
            if self.tags is None:
                self.tags = []
            self.tags.append(tag)
            
        elif len(tag) <= 20 and tag not in self.tags:
            self.tags.append(tag)

    def add_neural_network(self, key: str, value: str):
        """Add a neural network to the article."""
        if self.neural_networks is None:
            self.neural_networks = {}
        self.neural_networks[key] = value

    @classmethod
    def get_json(cls, json_data):
        return cls(
            id=json_data.get("id"),
            title=json_data.get("title"),
            body=json_data.get("body"),
            language_code=json_data.get("language_code"),
            language_to_answer_code=json_data.get("language_to_answer_code"),
            language_to_answer_name=json_data.get("language_to_answer_name"),
            theme_name=json_data.get("theme_name"),
            tags=json_data.get("tags", []),
            annotation=json_data.get("annotation"),
            neural_networks=json_data.get("neural_networks", {}),
            has_annotation=json_data.get("has_annotation", False)
        )