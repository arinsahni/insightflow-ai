"""Deterministic request-intent detection and grouping."""

from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


REQUEST_PATTERNS = (
    "please add", "need an option", "should have", "would be useful",
    "allow us to", "wish there was", "feature request", "add support for",
    "can you add", "it would be better if", "introduce a feature", "please introduce",
)
GROUP_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("Dark mode", ("dark mode",), "Dark mode"),
    ("Scheduled delivery", ("scheduled delivery", "schedule delivery", "scheduled ordering", "schedule an order"), "Scheduled ordering"),
    ("Reorder", ("reorder", "order again", "repeat order"), "Reorder"),
    ("Filters and sorting", ("filter", "sorting", "sort by"), "Better filters and sorting"),
    ("Personalization", ("personalization", "personalized", "recommendation"), "Personalization"),
    ("Multiple addresses", ("multiple address", "more addresses"), "Multiple addresses"),
    ("Tip customization", ("custom tip", "tip customization", "change tip"), "Tip customization"),
    ("Live delivery chat", ("live chat", "chat with rider", "delivery chat"), "Live delivery chat"),
)


@dataclass(frozen=True, slots=True)
class FeatureRequestResult:
    """Feature request outputs for one review."""

    is_feature_request: bool
    feature_request_text: str | None
    feature_request_confidence: float
    feature_request_group: str | None


def detect_feature_request(text: object) -> FeatureRequestResult:
    """Detect explicit request intent and normalize known request groups."""
    if text is None or pd.isna(text) or not str(text).strip():
        return FeatureRequestResult(False, None, 0.0, None)
    lowered = re.sub(r"\s+", " ", str(text).lower()).strip()
    intent_hits = sum(pattern in lowered for pattern in REQUEST_PATTERNS)
    if not intent_hits:
        return FeatureRequestResult(False, None, 0.0, None)
    for group, patterns, summary in GROUP_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return FeatureRequestResult(True, summary, min(1.0, 0.85 + 0.05 * intent_hits), group)
    return FeatureRequestResult(True, "Other requested capability", min(0.8, 0.65 + 0.05 * intent_hits), "Other feature request")


def add_feature_request_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with feature request detection fields."""
    output = dataframe.copy()
    results = [detect_feature_request(text) for text in output["clean_text"]]
    output["is_feature_request"] = [result.is_feature_request for result in results]
    output["feature_request_text"] = [result.feature_request_text for result in results]
    output["feature_request_confidence"] = [result.feature_request_confidence for result in results]
    output["feature_request_group"] = [result.feature_request_group for result in results]
    return output
