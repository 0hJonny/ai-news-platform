from dataclasses import dataclass
from typing import List

@dataclass
class ArticleQueueData:
    article_id: str
    native_language: str
    language_code: str
    language_name: str
    has_annotation: bool

@dataclass
class ArticleQueue:
    data: List[ArticleQueueData]
