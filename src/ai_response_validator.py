"""Validate model output against the exact compact evidence payload."""

from __future__ import annotations

import math
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.ai_response_models import ExecutiveInsightsResponse


HYPOTHESIS_MARKERS = (
    "hypothesis", "may ", "might ", "could ", "possible", "plausible",
    "investigate", "validate whether", "suggests",
)
NON_ASSERTION_MARKERS = (
    "no ", "not ", "unknown", "unavailable", "was not supplied",
    "does not establish", "cannot establish",
)
UNSUPPORTED_BUSINESS_TERMS = ("revenue", "retention", "conversion", "churn")
CAUSAL_PATTERNS = (
    r"\bcaused by\b", r"\bdue to\b", r"\bresulted in\b", r"\bled to\b",
    r"\bdrives?\b", r"\broot cause\b",
)
NUMBER_PATTERN = re.compile(r"(?<![\w.-])(-?\d[\d,]*(?:\.\d+)?)\s*(%)?")


class EvidenceValidationResult(BaseModel):
    """Inspectable grounding result returned without modifying model output."""

    model_config = ConfigDict(extra="forbid")
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    validated_review_ids: list[str] = Field(default_factory=list)
    invalid_review_ids: list[str] = Field(default_factory=list)
    unsupported_metrics: list[str] = Field(default_factory=list)


def _walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    else:
        yield path, value


def _payload_evidence(payload: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    ids: set[str] = set()
    quotes: dict[str, str] = {}
    for path, value in _walk(payload):
        if path.endswith("review_id") and value is not None:
            ids.add(str(value))
        elif "review_ids[" in path and value is not None:
            ids.add(str(value))
    for quote in payload.get("representative_quotes", []):
        identifier = str(quote.get("review_id", ""))
        if identifier:
            ids.add(identifier)
            quotes[identifier] = str(quote.get("review_text", ""))
    return ids, quotes


def _numeric_values(payload: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for path, value in _walk(payload):
        if path.endswith(".rank") or path.endswith("source_row_index"):
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        number = float(value)
        if math.isfinite(number):
            values.append(number)
    return values


def _number_supported(number: float, percent: bool, allowed: list[float]) -> bool:
    candidates = [number / 100.0, number] if percent else [number, number / 100.0]
    for candidate in candidates:
        for source in allowed:
            tolerance = max(0.011, abs(source) * 0.012)
            if abs(candidate - source) <= tolerance:
                return True
    return False


def _response_strings(response: ExecutiveInsightsResponse):
    payload = response.model_dump(mode="python")
    for path, value in _walk(payload):
        if isinstance(value, str):
            yield path, value


def validate_executive_response(
    response: ExecutiveInsightsResponse,
    context_payload: dict[str, Any],
) -> EvidenceValidationResult:
    """Reject invented IDs, quotes, measured metrics, and unsupported causality."""
    available_ids, exact_quotes = _payload_evidence(context_payload)
    cited_ids: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    unsupported: list[str] = []

    response_payload = response.model_dump(mode="python")
    for path, value in _walk(response_payload):
        if path.endswith("supporting_review_ids") or not isinstance(value, str):
            continue
        if "supporting_review_ids[" in path:
            cited_ids.append(value)
    for reference in response.evidence:
        cited_ids.append(reference.review_id)
        expected = exact_quotes.get(reference.review_id)
        if expected is None:
            errors.append(
                f"Evidence quote for {reference.review_id} is unavailable in the compact quote evidence."
            )
        elif reference.quote != expected:
            errors.append(f"Evidence quote for {reference.review_id} is not exact source text.")

    invalid_ids = sorted(set(cited_ids) - available_ids)
    if invalid_ids:
        errors.append("Generated report cited review IDs absent from the supplied context.")

    allowed_numbers = _numeric_values(context_payload)
    for path, text in _response_strings(response):
        lowered = text.lower()
        hypothetical = any(marker in lowered for marker in HYPOTHESIS_MARKERS)
        non_assertive = any(marker in lowered for marker in NON_ASSERTION_MARKERS)
        if (
            any(term in lowered for term in UNSUPPORTED_BUSINESS_TERMS)
            and not hypothetical and not non_assertive
        ):
            errors.append(f"Unsupported business-impact claim in {path}.")
        if (
            any(re.search(pattern, lowered) for pattern in CAUSAL_PATTERNS)
            and not hypothetical and not non_assertive
        ):
            errors.append(f"Unsupported causal claim in {path}.")
        if path.endswith(("timeframe", "owner", "title")):
            continue
        for match in NUMBER_PATTERN.finditer(text):
            number = float(match.group(1).replace(",", ""))
            if _number_supported(number, bool(match.group(2)), allowed_numbers):
                continue
            claim = match.group(0).strip()
            unsupported.append(f"{path}: {claim}")
            if match.group(2) or any(
                token in lowered
                for token in ("reviews", "feedback", "requests", "mentions", "rating", "score")
            ):
                errors.append(f"Unsupported measured value {claim!r} in {path}.")
            else:
                warnings.append(f"Ambiguous numeric value {claim!r} in {path}.")

    if not response.confidence_assessment.limitations:
        errors.append("Confidence assessment must include limitations.")

    return EvidenceValidationResult(
        valid=not errors,
        errors=list(dict.fromkeys(errors)),
        warnings=list(dict.fromkeys(warnings)),
        validated_review_ids=sorted(set(cited_ids) & available_ids),
        invalid_review_ids=invalid_ids,
        unsupported_metrics=list(dict.fromkeys(unsupported)),
    )
