from .ServerInterface import ServerInterface
from models import ArticleAnnotation, ArticleQueueData, User


class Client:
    def __init__(self, article_id: str):
        self.user = User()
        self.user.set_token(ServerInterface.login(self.user.get_login(), self.user.get_password())[0])
        self.get_article(article_id)
        
    def get_article(self, articleQueueData: ArticleQueueData):
        self.article = ArticleAnnotation.get_json(ServerInterface.get_article(articleQueueData["article_id"], self.user.get_token())[0])
        self.article.language_code = articleQueueData["native_language"]
        self.article.language_to_answer_code = articleQueueData["language_code"]
        self.article.language_to_answer_name = articleQueueData["language_name"]
        self.article.title_orig = self.article.title

    def send_article(self) -> bool:
        if self.article.check_article_annotation_error() is not None:
            return False 

        if ServerInterface.send_annotation(self.article, self.user.get_token()) == 201:
            return True
        else:
            raise "Server error!"
