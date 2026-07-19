"""Backward-compatible exports for deterministic feature-request classification."""

from src.feature_request_classifier import (
    FEATURE_REQUEST_GROUPS,
    FEATURE_REQUEST_TAXONOMY,
    FeatureRequestResult,
    add_feature_request_columns,
    detect_feature_request,
    normalize_feature_request_text,
)

__all__ = (
    "FEATURE_REQUEST_GROUPS",
    "FEATURE_REQUEST_TAXONOMY",
    "FeatureRequestResult",
    "add_feature_request_columns",
    "detect_feature_request",
    "normalize_feature_request_text",
)
