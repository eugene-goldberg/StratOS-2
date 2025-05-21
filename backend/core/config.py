import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict # Import SettingsConfigDict

class Settings(BaseSettings):
    """Application settings"""
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    # API configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "StratOS"
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Cosmos DB configuration
    AZURE_COSMOS_ENDPOINT: Optional[str] = os.getenv("AZURE_COSMOS_ENDPOINT")
    AZURE_COSMOS_KEY: Optional[str] = os.getenv("AZURE_COSMOS_KEY")
    AZURE_COSMOS_DATABASE_NAME: str = os.getenv("AZURE_COSMOS_DATABASE_NAME", "stratosdb")

settings = Settings()
