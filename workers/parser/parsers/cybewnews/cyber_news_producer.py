import logging
from bs4 import BeautifulSoup
from parsers.base_parser import BaseParser

logging.basicConfig(filename='CyberNews.log', level=logging.INFO)
logger = logging.getLogger(__name__)

class CyberNewsProducer(BaseParser):
    def __init__(self, base_url: str, language_code: str, queue):
        super().__init__()
        self.base_url = base_url
        self.language_code = language_code
        self.queue = queue
        self.max_duplicates = 13

    def start(self):
        page_number = 0
        same_articles = 0
        
        while True:
            page_number += 1
            url = f"{self.base_url}/page/{page_number}" if page_number > 1 else self.base_url
            logger.info(f"[Producer] Parsing page: {url}")
            
            html_content = self._fetch_html(url)
            if not html_content:
                break
                
            soup = BeautifulSoup(html_content, "lxml")
            posts_container = soup.find("div", class_="cells_space_xl")
            if not posts_container:
                break
            
            posts_container = posts_container.parent
            posts_hrefs = []

            # Focus articles
            for a in posts_container.find_all("a", class_="focus-articles__link"):
                posts_hrefs.append(a.get('href'))

            # Regular articles
            for h3 in posts_container.find_all("h3", class_="heading"):
                parent_a = h3.parent
                if parent_a and parent_a.name == 'a':
                    posts_hrefs.append(parent_a.get('href'))

            if not posts_hrefs:
                break

            for href in posts_hrefs:
                if self._check_article_href(href):
                    same_articles += 1
                    if same_articles >= self.max_duplicates:
                        logger.info(f"[Producer] Reached limit of existing articles for {self.base_url}.")
                        return # Stop the producer
                    continue
                
                # Push to the queue (URL, language)
                logger.info(f"[Producer] Found new article: {href}")
                self.queue.put((href, self.language_code))