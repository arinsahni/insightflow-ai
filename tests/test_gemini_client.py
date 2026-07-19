"""Network-free tests for the lazy Google Gen AI client boundary."""

from types import SimpleNamespace

import pytest

from src.gemini_client import (
    GeminiAuthenticationError, GeminiConfigurationError, GeminiExecutiveClient,
    GeminiRateLimitError, GeminiResponseError, GeminiTimeoutError,
)
from tests.test_ai_response_models import valid_response


class ApiError(Exception):
    def __init__(self, status_code: int, message: str = "safe") -> None:
        self.status_code = status_code
        super().__init__(message)


class FakeModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _response(parsed=None, text=None, usage=True):
    metadata = SimpleNamespace(
        prompt_token_count=100, candidates_token_count=50,
        total_token_count=150, cached_content_token_count=10,
    ) if usage else None
    return SimpleNamespace(
        parsed=parsed, text=text, usage_metadata=metadata,
        candidates=[SimpleNamespace(finish_reason="STOP")],
    )


def test_missing_key_is_lazy_and_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    calls = []
    client = GeminiExecutiveClient(client_factory=lambda **kwargs: calls.append(kwargs))
    assert not client.is_configured and calls == []
    with pytest.raises(GeminiConfigurationError):
        client.generate_executive_insights("prompt")
    assert calls == []


def test_success_uses_model_schema_timeout_and_usage() -> None:
    models = FakeModels([_response(parsed=valid_response())])
    factory_calls = []
    client = GeminiExecutiveClient(
        api_key="test-value", model="test-model", timeout_seconds=12,
        client_factory=lambda **kwargs: factory_calls.append(kwargs) or SimpleNamespace(models=models),
    )
    result, usage = client.generate_executive_insights("prompt")
    assert result.executive_summary
    assert models.calls[0]["model"] == "test-model"
    assert models.calls[0]["config"].response_schema is not None
    assert factory_calls[0]["http_options"].timeout == 12_000
    assert usage.total_token_count == 150 and usage.retry_count == 0


def test_missing_usage_is_safe_and_json_text_parses() -> None:
    models = FakeModels([_response(text=valid_response().model_dump_json(), usage=False)])
    client = GeminiExecutiveClient(
        api_key="x", client_factory=lambda **_: SimpleNamespace(models=models)
    )
    _, usage = client.generate_executive_insights("prompt")
    assert usage.total_token_count is None


@pytest.mark.parametrize(
    ("error", "expected"),
    [(ApiError(401, "bad key x"), GeminiAuthenticationError),
     (ApiError(429), GeminiRateLimitError), (ApiError(408), GeminiTimeoutError)],
)
def test_error_mapping_and_nonretryable_behavior(error, expected) -> None:
    models = FakeModels([error, error, error])
    client = GeminiExecutiveClient(
        api_key="secret-key", max_retries=0,
        client_factory=lambda **_: SimpleNamespace(models=models),
    )
    with pytest.raises(expected) as raised:
        client.generate_executive_insights("prompt")
    assert "secret-key" not in str(raised.value)
    assert len(models.calls) == 1


def test_transient_retry_count_and_delays() -> None:
    models = FakeModels([ApiError(503), ApiError(429), _response(parsed=valid_response())])
    delays = []
    client = GeminiExecutiveClient(
        api_key="x", max_retries=2, sleep_fn=delays.append,
        client_factory=lambda **_: SimpleNamespace(models=models),
    )
    _, usage = client.generate_executive_insights("prompt")
    assert usage.retry_count == 2
    assert delays == [1.0, 2.0]


def test_malformed_response_raises_safe_error() -> None:
    models = FakeModels([_response(text="{bad json")])
    client = GeminiExecutiveClient(
        api_key="x", client_factory=lambda **_: SimpleNamespace(models=models)
    )
    with pytest.raises(GeminiResponseError):
        client.generate_executive_insights("prompt")

