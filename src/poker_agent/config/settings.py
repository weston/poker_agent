"""Application settings and configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    default_model: str = "claude-sonnet-4-20250514"

    # PT4 Database Configuration
    pt4_db_host: str = "localhost"
    pt4_db_port: int = 5432
    pt4_db_name: str = "pt4_db"
    pt4_db_user: str = "postgres"
    pt4_db_password: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def pt4_connection_string(self) -> str:
        """Get PostgreSQL connection string for PT4 database."""
        return (
            f"postgresql://{self.pt4_db_user}:{self.pt4_db_password}"
            f"@{self.pt4_db_host}:{self.pt4_db_port}/{self.pt4_db_name}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
