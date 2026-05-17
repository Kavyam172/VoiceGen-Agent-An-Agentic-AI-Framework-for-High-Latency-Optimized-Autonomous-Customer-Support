"""
settings.py — Centralised application configuration.

Reads all configuration from environment variables (via .env file).
Uses Pydantic BaseSettings so every setting is type-validated at
startup; the application fails fast with a clear error if something
is missing or has the wrong type.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Resolve the .env file path relative to THIS file so it works regardless
# of the current working directory when the module is first imported.
# settings.py lives at:  customer_support_agent/app/config/settings.py
# .env lives at:         customer_support_agent/.env
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All values can be overridden by setting the corresponding
    environment variable or by editing the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── OpenAI / LLM ────────────────────────────────────────────────
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (sk-…). Required for LLM calls.",
    )
    model_name: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name to use for all LLM calls.",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for the LLM.",
    )
    max_tokens: int = Field(
        default=512,
        gt=0,
        description="Maximum number of tokens in the LLM response.",
    )

    # ── Logging ─────────────────────────────────────────────────────
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG | INFO | WARNING | ERROR).",
    )

    # ── Application metadata ─────────────────────────────────────────
    app_name: str = Field(
        default="Customer Support AI Assistant",
        description="Human-readable application name shown in the UI.",
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version string.",
    )


# ---------------------------------------------------------------------------
# Module-level singleton — import this object everywhere instead of
# instantiating Settings() repeatedly.
# ---------------------------------------------------------------------------
settings = Settings()
