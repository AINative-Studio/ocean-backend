"""Application Configuration"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ZeroDB Configuration
    ZERODB_API_URL: str
    ZERODB_PROJECT_ID: str
    ZERODB_API_KEY: str

    # Ocean Configuration
    OCEAN_EMBEDDINGS_MODEL: str = "BAAI/bge-base-en-v1.5"
    OCEAN_EMBEDDINGS_DIMENSIONS: int = 768

    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Ocean Backend"
    DEBUG: bool = False

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000"
    ]

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
