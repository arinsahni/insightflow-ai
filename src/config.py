"""Central, environment-backed application configuration."""

from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse a conventional environment boolean with a safe default."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AppSettings(BaseModel):
    """Validated runtime settings loaded from environment variables."""

    model_config = ConfigDict(frozen=True)

    app_name: str = "InsightFlow AI"
    subtitle: str = "Turn customer feedback into product decisions"
    gemini_api_key: str | None = Field(default=None, repr=False)
    gemini_model: str = DEFAULT_GEMINI_MODEL
    enable_ai: bool = True
    max_ai_quotes_per_theme: int = Field(default=5, ge=1, le=20)
    gemini_timeout_seconds: int = Field(default=45, ge=5, le=180)
    gemini_max_retries: int = Field(default=2, ge=0, le=5)
    max_upload_rows: int = Field(default=50_000, ge=1)

    @property
    def ai_available(self) -> bool:
        """Return whether optional AI is enabled and has a credential."""
        return self.enable_ai and bool(self.gemini_api_key)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Load and validate application settings without requiring an API key."""
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip() or None
    model = os.getenv("GEMINI_MODEL", "").strip() or DEFAULT_GEMINI_MODEL
    return AppSettings(
        gemini_api_key=api_key,
        gemini_model=model,
        enable_ai=_parse_bool(os.getenv("ENABLE_AI"), default=True),
        max_ai_quotes_per_theme=int(os.getenv("MAX_AI_QUOTES_PER_THEME", "5")),
        gemini_timeout_seconds=int(os.getenv("GEMINI_TIMEOUT_SECONDS", "45")),
        gemini_max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "2")),
        max_upload_rows=int(os.getenv("MAX_UPLOAD_ROWS", "50000")),
    )
