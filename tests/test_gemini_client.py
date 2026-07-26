"""Network-free tests for the lazy Google Gen AI client boundary."""

from types import SimpleNamespace

import pytest

from src.gemini_client import (
    GeminiAuthenticationError, GeminiConfigurationError, GeminiExecutiveClient,
    GeminiRateLimitError, GeminiRequestError, GeminiResponseError,
    GeminiTimeoutError, executive_response_transport_schema,
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
    config = models.calls[0]["config"]
    assert config.response_schema is None
    assert config.response_json_schema is not None
    assert config.thinking_config.thinking_budget == 0
    assert factory_calls[0]["http_options"].timeout == 12_000
    assert usage.total_token_count == 150 and usage.retry_count == 0


def test_transport_schema_keeps_shape_without_unsupported_constraints() -> None:
    """The API schema stays simple while local Pydantic remains strict."""
    schema = executive_response_transport_schema()
    serialized = str(schema)
    assert "executive_summary" in schema["properties"]
    assert "additionalProperties" not in serialized
    assert "minLength" not in serialized
    assert "maxItems" not in serialized
    assert "$defs" in schema


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
        api_key="x", max_retries=0,
        client_factory=lambda **_: SimpleNamespace(models=models)
    )
    with pytest.raises(GeminiResponseError):
        client.generate_executive_insights("prompt")


def test_invalid_response_retries_and_then_succeeds() -> None:
    models = FakeModels([
        _response(text="{bad json"),
        _response(parsed=valid_response()),
    ])
    delays = []
    client = GeminiExecutiveClient(
        api_key="x", max_retries=1, sleep_fn=delays.append,
        client_factory=lambda **_: SimpleNamespace(models=models),
    )
    result, usage = client.generate_executive_insights("prompt")
    assert result.executive_summary
    assert usage.retry_count == 1
    assert delays == [1.0]


def test_max_token_response_raises_specific_safe_error() -> None:
    response = _response(text='{"executive_summary":"cut')
    response.candidates[0].finish_reason = "MAX_TOKENS"
    client = GeminiExecutiveClient(
        api_key="x", max_retries=0, client_factory=lambda **_: SimpleNamespace(
            models=FakeModels([response])
        )
    )
    with pytest.raises(GeminiResponseError, match="output limit"):
        client.generate_executive_insights("prompt")


def test_invalid_argument_preserves_safe_root_cause() -> None:
    error = ApiError(400, 'additional_properties rejected; key=do-not-copy')
    client = GeminiExecutiveClient(
        api_key="do-not-copy", max_retries=2,
        client_factory=lambda **_: SimpleNamespace(models=FakeModels([error])),
    )
    with pytest.raises(GeminiRequestError) as raised:
        client.generate_executive_insights("prompt")
    assert "structured-output schema" in str(raised.value)
    assert "do-not-copy" not in str(raised.value)
    assert raised.value.__cause__ is error
