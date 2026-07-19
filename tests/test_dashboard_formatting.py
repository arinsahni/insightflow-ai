"""Tests for presentation-only dashboard view models."""

import pandas as pd

from src.dashboard_formatting import curated_feedback_table, executive_theme_table, format_kpi_value


def test_kpi_formatting_handles_missing_values() -> None:
    assert format_kpi_value(None) == "Not available"
    assert format_kpi_value(12.345, decimals=1, suffix="%") == "12.3%"


def test_executive_theme_table_is_curated_and_sorted() -> None:
    source = pd.DataFrame({
        "theme": ["A", "B"], "frequency": [2, 4], "share_percentage": [33.333, 66.667],
        "average_rating": [2.5, 3.5], "negative_percentage": [80.123, 20.456],
        "severity_score": [70.12, 50.12], "priority_score": [65.8, 72.2],
        "priority_label": ["P1 High", "P1 High"], "business_risk": ["Trust risk", "Retention risk"],
        "average_confidence": [0.8, 0.9],
    })
    result = executive_theme_table(source)
    assert result.columns.tolist() == ["Theme", "Mentions", "Share", "Avg. Rating", "Negative Feedback", "Severity", "Priority", "Priority Level", "Business Risk"]
    assert result.iloc[0]["Theme"] == "B"
    assert result.iloc[0]["Share"] == 66.7


def test_curated_feedback_uses_only_reader_fields() -> None:
    source = pd.DataFrame({
        "review_id": ["1"], "original_text": ["Exact quote"], "clean_text": ["clean"],
        "rating": [4], "sentiment": ["Positive"], "primary_theme": ["Positive Feedback"],
        "subtheme": ["General praise"], "platform": ["iOS"], "app_version": ["1.0"],
        "date": pd.to_datetime(["2025-01-01"]), "sentiment_score": [0.8],
    })
    result = curated_feedback_table(source)
    assert result.columns.tolist() == ["Review ID", "Feedback", "Rating", "Sentiment", "Theme", "Subtheme", "Platform", "App Version", "Date"]
    assert result.iloc[0]["Date"] == "2025-01-01"
