"""Central, environment-backed application configuration."""

from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

# Load local development values once. Streamlit Community Cloud does not use
# this file; its secrets are resolved separately below. Loading once also keeps
# tests and runtime overrides deterministic.
load_dotenv(PROJECT_ROOT / ".env", override=False)


def _parse_bool(value: str | None, *, default: bool) -> bool:
    """Parse a conventional environment boolean with a safe default."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _streamlit_secrets() -> dict[str, object]:
    """Return configured Streamlit secrets without requiring a secrets file."""
    try:
        import streamlit as st

        return st.secrets.to_dict()
    except Exception:
        # Streamlit raises when no secrets file or runtime context is present.
        return {}


def _setting_value(name: str, secrets: dict[str, object]) -> str | None:
    """Resolve an environment variable first, then a top-level Streamlit secret."""
    environment_value = os.getenv(name)
    if environment_value is not None:
        return environment_value.strip()
    secret_value = secrets.get(name)
    return str(secret_value).strip() if secret_value is not None else None


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
    """Load environment or Streamlit settings without requiring an API key."""
    secrets = _streamlit_secrets()
    api_key = _setting_value("GEMINI_API_KEY", secrets) or None
    model = _setting_value("GEMINI_MODEL", secrets) or DEFAULT_GEMINI_MODEL
    return AppSettings(
        gemini_api_key=api_key,
        gemini_model=model,
        enable_ai=_parse_bool(_setting_value("ENABLE_AI", secrets), default=True),
        max_ai_quotes_per_theme=int(
            _setting_value("MAX_AI_QUOTES_PER_THEME", secrets) or "5"
        ),
        gemini_timeout_seconds=int(
            _setting_value("GEMINI_TIMEOUT_SECONDS", secrets) or "45"
        ),
        gemini_max_retries=int(
            _setting_value("GEMINI_MAX_RETRIES", secrets) or "2"
        ),
        max_upload_rows=int(_setting_value("MAX_UPLOAD_ROWS", secrets) or "50000"),
    )
