"""
Configuration Settings for Testing Agent Platform.
Loads environment variables from .env with Pydantic V2 BaseSettings.
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General Settings
    APP_NAME: str = "AI Testing Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server Settings
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    FRONTEND_PORT: int = 4200

    # Security
    SECRET_KEY: str = "dev_secret_key_testing_agent_platform_2026_local"
    APP_MASTER_KEY: Optional[str] = Field(default=None, description="Master key for encrypted secrets vault")
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "testserver"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:4201",
        "http://127.0.0.1:4201",
    ]
    MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB max upload
    MAX_ZIP_DECOMPRESSED_BYTES: int = 50 * 1024 * 1024  # 50 MB max decompressed
    MAX_ZIP_FILES: int = 500

    # Database
    DATABASE_URL: str = Field(
        default=f"sqlite:///{BASE_DIR / 'testing_platform.db'}",
        description="SQLAlchemy Database Connection URL"
    )

    # AI Provider API Keys
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API Key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API Key")

    # Default Agent Models
    DEFAULT_GEMINI_MODEL: str = "gemini-2.5-flash"
    DEFAULT_OPENAI_MODEL: str = "gpt-4o-mini"
    DEFAULT_PROVIDER: str = "gemini"

    # Storage Paths
    BASE_DIR: Path = BASE_DIR
    ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
    LOGS_DIR: Path = BASE_DIR / "logs"

    # Execution Sandbox Settings
    TEST_EXECUTION_TIMEOUT_SECONDS: int = 120
    MAX_CONCURRENT_TESTS: int = 4
    ALLOW_HEADLESS_BROWSER: bool = True


settings = Settings()
