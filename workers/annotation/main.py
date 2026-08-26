import copy


from utils import Client, QueueManager
from services import ArticleService, Logger
from models.GenerationModels import OpenChat, Gemma_2b, Gemma_7b, Mistral, Gemma_4b_e4b

# Configure logging

def main():
    logger = Logger("logs/app.log")
    Manager = QueueManager()
    for queue in Manager.articles_queue:
        Worker = Client(queue)
        article_copy = copy.deepcopy(Worker.article)
        print(article_copy)
        # return
        for attempt in range(3):
            try:
                Worker.article = copy.deepcopy(article_copy)
                if not Worker.article.has_annotation:
                    Worker.article = ArticleService().extract_tags(Worker.article, model=Gemma_4b_e4b())
                    Worker.article = ArticleService().categorize(Worker.article, model=Gemma_4b_e4b())
                Worker.article = ArticleService().annotate(Worker.article, model=Gemma_4b_e4b())
                if Worker.article.language_to_answer_code != Worker.article.language_code:
                    Worker.article = ArticleService().translate(Worker.article, model=Gemma_4b_e4b())
                print(Worker.article.check_article_annotation_error())
                if Worker.send_article():
                    logger.info("Article has been sent to server. Article: %s" % Worker.article.__dict__)
                    break
                logger.error("Cannot send Article to server. Article: %s" % Worker.article.__dict__)
            except TypeError:
                logger.error(f"Attempt {attempt+1} failed. Article: {Worker.article.__dict__}")
                if attempt == 2:
                    logger.error("All attempts failed. Get new article.")
                    continue
                else:
                    logger.error("Next attempt.")

if __name__ == "__main__":
    main()
