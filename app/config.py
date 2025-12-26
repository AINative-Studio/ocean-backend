"""Application Configuration"""

from typing import List, Optional
from pydantic_settings import BaseSettings
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ZeroDB Configuration
    ZERODB_API_URL: str = "https://api.ainative.studio"
    ZERODB_PROJECT_ID: Optional[str] = None
    ZERODB_API_KEY: Optional[str] = None

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
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True

    def validate_zerodb_config(self) -> bool:
        """Check if ZeroDB configuration is complete."""
        return bool(self.ZERODB_PROJECT_ID and self.ZERODB_API_KEY)


# Create settings instance
settings = Settings()
