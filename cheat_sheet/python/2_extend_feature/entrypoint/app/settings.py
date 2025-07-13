from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration using pydantic-settings."""

    model_config = SettingsConfigDict(
        env_prefix="WORKSHOP_", env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    env: Literal["local", "staging", "production"] = Field(default="staging", description="The running environment")

    log_level: Literal["error", "warn", "info", "debug", "disabled"] = Field(
        default="info", description="Log filtering level"
    )

    port: int = Field(default=8080, description="The HTTP server port", ge=1, le=65535)
