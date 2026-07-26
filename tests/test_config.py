"""Tests for environment and Streamlit-backed configuration."""

from src import config
from src.config import DEFAULT_GEMINI_MODEL, get_settings


def test_defaults_work_without_gemini_key(monkeypatch) -> None:
    """The app must remain usable when Gemini is not configured."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("ENABLE_AI", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gemini_api_key is None
    assert settings.gemini_model == DEFAULT_GEMINI_MODEL
    assert settings.enable_ai is True
    assert settings.ai_available is False


def test_environment_overrides_are_validated(monkeypatch) -> None:
    """Supported environment variables should override safe defaults."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-value")
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("ENABLE_AI", "false")
    monkeypatch.setenv("MAX_AI_QUOTES_PER_THEME", "7")
    monkeypatch.setenv("MAX_UPLOAD_ROWS", "1234")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gemini_model == "test-model"
    assert settings.enable_ai is False
    assert settings.max_ai_quotes_per_theme == 7
    assert settings.max_upload_rows == 1234
    assert settings.ai_available is False


def test_api_availability_requires_enable_flag_and_key(monkeypatch) -> None:
    """AI status should be true only when both conditions are satisfied."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-value")
    monkeypatch.setenv("ENABLE_AI", "true")
    get_settings.cache_clear()

    assert get_settings().ai_available is True


def test_streamlit_secrets_are_used_when_environment_is_absent(monkeypatch) -> None:
    """Community Cloud secrets should configure optional AI safely."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(
        config,
        "_streamlit_secrets",
        lambda: {"GEMINI_API_KEY": "streamlit-test-value", "GEMINI_MODEL": "cloud-model"},
    )
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.gemini_api_key == "streamlit-test-value"
    assert settings.gemini_model == "cloud-model"
    assert settings.ai_available is True


def teardown_module() -> None:
    """Prevent cached test settings from leaking to other test modules."""
    get_settings.cache_clear()
