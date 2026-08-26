from typing import List, Tuple, Optional
import requests
import os

from models import ArticleAnnotation

class ServerInterface:
    api_base_url: str = os.getenv("GOLANG_API")

    @staticmethod
    def get_articles_queue(user_token: str) -> List[dict]:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{ServerInterface.api_base_url}/p/annotation/queue", headers=headers)
        return response.json()

    @staticmethod
    def get_article(article_id: str, user_token: str) -> Tuple[dict, int]:
        headers = {"Authorization": f"Bearer {user_token}"}
        response = requests.get(f"{ServerInterface.api_base_url}/p/article/{article_id}", headers=headers)
        return response.json().get("data"), response.status_code

    @staticmethod
    def send_annotation(article: ArticleAnnotation, user_token: str) -> int:
        headers = {"Authorization": f"Bearer {user_token}"}
        data = article.__dict__
        response = requests.post(
            f"{ServerInterface.api_base_url}/p/annotation",
            headers=headers,
            json=data,
        )
        return response.status_code

    @staticmethod
    def login(username: str, password: str) -> Tuple[Optional[str], int]:
        login_url = f"{ServerInterface.api_base_url}/auth/login"
        login_data = {
            "username": username,
            "password": password
        }
        login_response = requests.post(login_url, json=login_data)
        user_token = login_response.json().get("data").get("jwt_token")
        return user_token, login_response.status_code
