import os
import time
import random
import cloudscraper
import requests

class BaseParser:
    def __init__(self):
        # Initialize the scraper in this specific process
        self.platforms = ['linux', 'windows', 'darwin', 'android']
        self.browsers = ['chrome', 'firefox']
        self.scraper = cloudscraper.create_scraper(
            delay=6, 
            browser={"browser": random.choice(self.browsers), "platform": random.choice(self.platforms)}
        )
        
        self.api_user_login: str = os.getenv("API_USER_LOGIN")
        self.api_user_password: str = os.getenv("API_USER_PASSWORD")
        self.api_base_url: str = os.getenv("GOLANG_API")
        self.api_access_token: str = ""
        self._login()

    def _login(self):
        login_url = f"{self.api_base_url}/auth/login"
        login_data = {"username": self.api_user_login, "password": self.api_user_password}
        try:
            response = requests.post(login_url, json=login_data, timeout=10)
            response.raise_for_status()
            self.api_access_token = response.json().get("data", {}).get("jwt_token", "")
        except Exception as e:
            print(f"Auth Error: {e}")

    def _fetch_html(self, url: str) -> bytes:
        max_attempts = 3
        for _ in range(max_attempts):
            time.sleep(random.uniform(1.0, 2.5))
            try:
                with self.scraper.get(url, timeout=10) as response:
                    response.raise_for_status()
                    return response.content
            except Exception as e:
                print(f"Request Error for {url}: {e}")
            max_attempts -= 1
        return None

    def _check_article_href(self, href: str) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_access_token}"}
            response = requests.get(
                f"{self.api_base_url}/p/article/check", 
                json={"article_href": href}, 
                headers=headers, 
                timeout=5
            )
            response.raise_for_status()
            return response.json().get("data", {}).get("exists", False)
        except Exception as e:
            print(f"Check Href Error: {e}")
            return True # On error, better to skip to avoid duplicates

    def _send_data_to_server(self, data: dict) -> bool:
        try:
            headers = {"Authorization": f"Bearer {self.api_access_token}"}
            response = requests.post(
                f"{self.api_base_url}/p/article", 
                json=data, 
                headers=headers, 
                timeout=5
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Send Data Error: {e}")
            return False