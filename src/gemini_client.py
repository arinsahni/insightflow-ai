"""Lazy, bounded, privacy-conscious Google Gen AI client boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import json
import logging
import os
from time import perf_counter, sleep
from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from src.ai_response_models import ExecutiveInsightsResponse, GeminiUsageMetadata
from src.config import DEFAULT_GEMINI_MODEL


LOGGER = logging.getLogger(__name__)


class GeminiError(RuntimeError):
    """Safe base exception for optional Gemini failures."""


class GeminiConfigurationError(GeminiError):
    pass


class GeminiAuthenticationError(GeminiError):
    pass


class GeminiRateLimitError(GeminiError):
    pass


class GeminiTimeoutError(GeminiError):
    pass


class GeminiServiceError(GeminiError):
    pass


class GeminiResponseError(GeminiError):
    pass


def _secret_value(secrets: Mapping[str, Any] | None, key: str) -> str | None:
    if not secrets:
        return None
    value = secrets.get(key)
    return str(value).strip() if value is not None and str(value).strip() else None


def get_gemini_api_key(
    explicit: str | None = None,
    *,
    secrets: Mapping[str, Any] | None = None,
) -> str | None:
    """Resolve a key by explicit, Streamlit-secret, then environment precedence."""
    return (
        (explicit or "").strip()
        or _secret_value(secrets, "GEMINI_API_KEY")
        or os.getenv("GEMINI_API_KEY", "").strip()
        or None
    )


def get_gemini_model(
    explicit: str | None = None,
    *,
    secrets: Mapping[str, Any] | None = None,
) -> str:
    """Resolve a model by explicit, Streamlit-secret, env, then default precedence."""
    return (
        (explicit or "").strip()
        or _secret_value(secrets, "GEMINI_MODEL")
        or os.getenv("GEMINI_MODEL", "").strip()
        or DEFAULT_GEMINI_MODEL
    )


def streamlit_secrets_safe() -> Mapping[str, Any] | None:
    """Read Streamlit secrets only when called by UI code and configured."""
    try:
        import streamlit as st
        return st.secrets.to_dict()
    except Exception:
        # Streamlit raises its own configuration exception when no file exists.
        return None


def _status_code(error: Exception) -> int | None:
    for candidate in (getattr(error, "status_code", None), getattr(error, "code", None)):
        try:
            return int(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _map_error(error: Exception) -> tuple[GeminiError, bool]:
    code = _status_code(error)
    name = type(error).__name__.lower()
    text = str(error).lower()
    if code in {401, 403} or "auth" in name or "api key" in text:
        return GeminiAuthenticationError(
            "Gemini authentication failed. Check the configured API key."
        ), False
    if code == 429 or "resourceexhausted" in name or "rate limit" in text:
        return GeminiRateLimitError(
            "Gemini is temporarily rate limited. Please try again shortly."
        ), True
    if code in {408, 504} or "timeout" in name or "timed out" in text:
        return GeminiTimeoutError(
            "Gemini did not respond before the request timeout."
        ), True
    if code is not None and 500 <= code < 600 or "serviceunavailable" in name:
        return GeminiServiceError(
            "Gemini is temporarily unavailable. Please try again later."
        ), True
    return GeminiServiceError(
        "Gemini could not complete the request. Please try again later."
    ), False


def _usage(response: Any, *, retries: int, latency: float) -> GeminiUsageMetadata:
    usage = getattr(response, "usage_metadata", None)
    candidate = (getattr(response, "candidates", None) or [None])[0]
    finish = getattr(candidate, "finish_reason", None)
    return GeminiUsageMetadata(
        prompt_token_count=getattr(usage, "prompt_token_count", None),
        output_token_count=(
            getattr(usage, "candidates_token_count", None)
            or getattr(usage, "output_token_count", None)
        ),
        total_token_count=getattr(usage, "total_token_count", None),
        cached_token_count=getattr(usage, "cached_content_token_count", None),
        retry_count=retries,
        latency_seconds=latency,
        finish_reason=str(finish) if finish is not None else None,
    )


class GeminiExecutiveClient:
    """Generate one schema-constrained executive response on explicit demand."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 45,
        max_retries: int = 2,
        client_factory: Callable[..., Any] = genai.Client,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        self.api_key = get_gemini_api_key(api_key)
        self.model = get_gemini_model(model)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)
        self._client_factory = client_factory
        self._sleep = sleep_fn
        self._client: Any | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self) -> Any:
        if not self.api_key:
            raise GeminiConfigurationError(
                "Gemini is not configured. Add an API key to enable generation."
            )
        if self._client is None:
            self._client = self._client_factory(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=self.timeout_seconds * 1_000),
            )
        return self._client

    def generate_executive_insights(
        self, prompt: str
    ) -> tuple[ExecutiveInsightsResponse, GeminiUsageMetadata]:
        """Call Gemini with no tools and validate the structured response locally."""
        client = self._get_client()
        started = perf_counter()
        LOGGER.info("Gemini request start model=%s prompt_chars=%d", self.model, len(prompt))
        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=6_000,
                        response_mime_type="application/json",
                        response_schema=ExecutiveInsightsResponse,
                        tools=None,
                    ),
                )
                parsed = getattr(response, "parsed", None)
                if isinstance(parsed, ExecutiveInsightsResponse):
                    result = parsed
                elif parsed is not None:
                    result = ExecutiveInsightsResponse.model_validate(parsed)
                else:
                    text = getattr(response, "text", None)
                    if not text:
                        raise GeminiResponseError(
                            "Gemini returned an empty structured response."
                        )
                    result = ExecutiveInsightsResponse.model_validate_json(text)
                metadata = _usage(
                    response, retries=attempt, latency=perf_counter() - started
                )
                LOGGER.info(
                    "Gemini request success model=%s latency=%.3f retries=%d",
                    self.model, metadata.latency_seconds, attempt,
                )
                return result, metadata
            except GeminiResponseError:
                raise
            except (ValidationError, json.JSONDecodeError, TypeError) as error:
                LOGGER.warning("Gemini response validation failed type=%s", type(error).__name__)
                raise GeminiResponseError(
                    "Gemini returned a response that did not match the required report structure."
                ) from None
            except Exception as error:
                mapped, retryable = _map_error(error)
                if retryable and attempt < self.max_retries:
                    LOGGER.warning("Gemini transient failure category=%s retry=%d", type(mapped).__name__, attempt + 1)
                    self._sleep(float(attempt + 1))
                    continue
                LOGGER.error("Gemini request failed category=%s retries=%d", type(mapped).__name__, attempt)
                raise mapped from None
        raise GeminiServiceError("Gemini could not complete the request.")
