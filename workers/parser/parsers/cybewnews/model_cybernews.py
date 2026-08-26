from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Article:
    title: str = None
    author: str = None
    post_href: str = None
    body: str = None
    image: str = None
    language: dict = field(default_factory=lambda: {"language_code": None})
    date: str = None # Store the already-formatted ISO string

    @property
    def is_valid(self) -> bool:
        """Checks that all required fields are present."""
        return all([self.title, self.author, self.post_href, self.body])