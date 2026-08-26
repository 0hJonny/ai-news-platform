import os
from dataclasses import dataclass


@dataclass
class User:
    api_user_login:str = os.getenv("API_USER_LOGIN")
    api_user_password:str = os.getenv("API_USER_PASSWORD")

    @classmethod
    def get_token(cls):
        return cls.api_access_token
    
    @classmethod
    def set_token(cls, token):
        cls.api_access_token = token
    
    @classmethod
    def get_login(cls):
        return cls.api_user_login
    
    @classmethod
    def get_password(cls):
        return cls.api_user_password