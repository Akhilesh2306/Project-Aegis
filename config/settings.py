"""File that contains all settings for the project"""

# Import External Libraries
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Setup project root and .env file path
PROJECT_ROOT = Path(__file__).parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Common config settings
_BASE_CONFIG = {
    "env_file": [".env", str(ENV_FILE_PATH)],
    "env_file_encoding": "utf-8",
    "case_sensitive": False,
    "extra": "ignore",
    "frozen": True,
}


class Settings(BaseSettings):
    """
    Settings for the project. This is a Pydantic BaseSettings class.
    """

    model_config = SettingsConfigDict(**_BASE_CONFIG)

    # Application settings
    app_name: str = "Project Aegis"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://aegis:aegis@localhost:5434/aegis"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_fast_model: str = "gpt-4o-mini"

    # Agent
    max_retries: int = 3
    drafting_max_tokens: int = 2000
    compliance_check_max_tokens: int = 4000

    # Storage
    s3_bucket: str = "aegis-contracts"
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
