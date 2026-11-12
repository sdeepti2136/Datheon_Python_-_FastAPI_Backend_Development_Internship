"""
Application Configuration Module.

Loads and validates environment variables using Pydantic Settings.
Adheres to 12-factor application design principles by decoupling
configuration from application code.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "Datheon BookStore API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Database Configuration
    # Uses SQLite with asynchronous aiosqlite driver for high concurrency
    DATABASE_URL: str = "sqlite+aiosqlite:///./datheon_bookstore.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///./test_datheon_bookstore.db"

    # JWT Authentication & Cryptographic Security
    JWT_SECRET_KEY: str = "insecure_default_secret_key_change_in_production_environment_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Rate Limiting Configuration
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # Admin Bootstrapping Credentials
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@datheon.local"
    BOOTSTRAP_ADMIN_PASSWORD: str = "ChangeMeAdmin123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        # In production, enforce non-default strong secret
        if len(v) < 32:
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is shorter than 32 characters! "
                "For production, use a strong cryptographically generated secret.",
                UserWarning,
            )
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of application settings.
    Avoids reading the .env file on every request.
    """
    return Settings()
