"""
Lender Matching Platform - Configuration
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/lender_matching"
    
    # AI (loaded from .env file: GEMINI_API_KEY=...)
    gemini_api_key: str = ""
    
    # App
    app_name: str = "Lender Matching Platform"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
