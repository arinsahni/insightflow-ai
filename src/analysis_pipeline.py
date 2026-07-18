"""Local Phase 3 analytics orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

import pandas as pd

from src.classifier import add_classification_columns
from src.feature_requests import add_feature_request_columns
from src.metrics import (
    OverallMetrics,
    calculate_feature_request_summary,
    calculate_overall_metrics,
    calculate_theme_summary,
)
from src.quotes import build_quote_index
from src.sentiment import add_sentiment_columns
from src.trends import TrendOutputs, calculate_trends


@dataclass(frozen=True, slots=True)
class AnalysisReport:
    """Processing counts and runtime for one local analysis."""

    input_rows: int
    analyzed_rows: int
    processing_time_seconds: float


@dataclass(slots=True)
class AnalysisResult:
    """Complete deterministic outputs for the Phase 3 application."""

    analyzed_reviews: pd.DataFrame
    overall_metrics: OverallMetrics
    theme_summary: pd.DataFrame
    feature_request_summary: pd.DataFrame
    trend_outputs: TrendOutputs
    representative_quotes: dict[str, list[dict[str, object]]]
    report: AnalysisReport
    warnings: list[str] = field(default_factory=list)


def analyze_feedback(dataframe: pd.DataFrame) -> AnalysisResult:
    """Run all local analytics without mutating input or using external APIs."""
    started = perf_counter()
    analyzed = add_sentiment_columns(dataframe)
    analyzed = add_feature_request_columns(analyzed)
    analyzed = add_classification_columns(analyzed)
    trends = calculate_trends(analyzed)
    theme_summary = calculate_theme_summary(analyzed, trends)
    overall = calculate_overall_metrics(analyzed, theme_summary, trends)
    feature_summary = calculate_feature_request_summary(analyzed)
    quote_index = build_quote_index(analyzed)
    warnings = list(trends.warnings)
    if len(analyzed) < 10:
        warnings.append("Small datasets may produce unstable summary metrics.")
    return AnalysisResult(
        analyzed, overall, theme_summary, feature_summary, trends, quote_index,
        AnalysisReport(len(dataframe), len(analyzed), perf_counter() - started),
        warnings,
    )
