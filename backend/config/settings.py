"""
Configuration management using Pydantic Settings.
Centralized configuration for the entire application.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Provides type-safe configuration access.
    """
    
    # Database Configuration
    DATABASE_URL: str
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "fraudai_db"
    DB_USER: str = "fraudai_user"
    DB_PASSWORD: str
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    SECRET_KEY: str
    
    # ML Model Configuration
    MODEL_PATH: str = "./intelligence/models/"
    RETRAIN_THRESHOLD: int = 1000
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_PATH: str = "./logs/"
    
    class Config:
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"


settings = Settings()
