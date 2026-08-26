import base64
from datetime import datetime
from bs4 import BeautifulSoup
import logging
from parsers import BaseParser
from .model_cybernews import Article

logger = logging.getLogger(__name__)

class CyberNewsConsumer(BaseParser):
    def __init__(self):
        super().__init__()

    def process_article(self, url: str, language_code: str):
        html = self._fetch_html(url)
        if not html:
            logger.error(f"[Consumer] Failed to fetch HTML for {url}")
            return

        soup = BeautifulSoup(html, "lxml")
        article = Article(post_href=url, language={"language_code": language_code})

        # 1. Parse the title
        # Look for an h1 with class heading_size_1
        h1_element = soup.find('h1', class_='heading')
        if h1_element:
            article.title = h1_element.get_text(strip=True)

        # 2. Parse the author
        author_link = soup.find('a', class_='article-info__link')
        if author_link:
            article.author = author_link.get_text(strip=True)

        # 3. Parse the date
        div_date = soup.find('div', class_='article-info__date')
        if div_date:
            date_str = div_date.get_text(strip=True)
            # Possible formats on the site (accounting for both Published and Updated)
            date_formats = [
                "Published: %d %B %Y", 
                "Updated on: %B %d, %Y %I:%M %p", 
                "Updated on: %B %d, %Y"
            ]
            
            for fmt in date_formats:
                try:
                    # Try to parse the date
                    parsed_date = datetime.strptime(date_str, fmt)
                    # Convert to ISO 8601 for the API
                    article.date = parsed_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    break
                except ValueError:
                    continue
            
            if not article.date:
                logger.warning(f"[Consumer] Unknown date format '{date_str}' on {url}")

        # 4. Parse the image
        # In the HTML, the image lives in figure.thumbnail.featured
        img_element = soup.select_one('figure.thumbnail.featured img')
        if img_element:
            img_src = img_element.get('src')
            if img_src:
                img_bytes = self._fetch_html(img_src)
                if img_bytes:
                    article.image = base64.b64encode(img_bytes).decode('utf-8')

        # 5. Parse the article body
        content_div = soup.find("div", class_="content")
        if content_div:
            # Remove ad blocks, scripts, and social links (to keep the text clean)
            for unwanted in content_div.select('.a-wrapper, script, .links-bar, .embed-wrapper'):
                unwanted.decompose()

            # Collect all text blocks: paragraphs and list items (for key takeaways)
            body_parts = []

            # If we need to preserve the takeaways structure, grab those too
            takeaways = content_div.find_all('div', class_='key-takeaway__list-text')
            for ta in takeaways:
                body_parts.append(f"- {ta.get_text(strip=True)}")

            # Grab regular paragraphs
            paragraphs = content_div.find_all('p', recursive=True)
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    body_parts.append(text)

            article.body = "\n\n".join(body_parts)

        # 6. Validate and send
        if article.is_valid:
            logger.info(f"[Consumer] Successfully parsed: {article.title}")
            success = self._send_data_to_server(article.__dict__)
            if not success:
                logger.error(f"[Consumer] Failed to send to server: {url}")
        else:
            logger.error(f"[Consumer] Validation failed (missing fields) for {url}")
            # Could log exactly what's missing here for debugging: