import os
from functools import lru_cache
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Application settings loaded from environment variables."""
    # DB
    DATABASE_URL: str = Field(default_factory=lambda: os.getenv("POSTGRES_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"))

    # Auth/JWT
    JWT_SECRET_KEY: str = Field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "change-me-in-prod"))
    JWT_ALGORITHM: str = Field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # CORS
    CORS_ORIGINS: str = Field(default_factory=lambda: os.getenv("CORS_ORIGINS", ""))

    # App
    LOG_LEVEL: str = Field(default_factory=lambda: os.getenv("REACT_APP_LOG_LEVEL", "INFO"))


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
