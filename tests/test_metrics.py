"""Tests for safe overall and theme metrics."""

import pandas as pd

from src.metrics import (
    calculate_feature_request_summary,
    calculate_overall_metrics,
    calculate_theme_summary,
)
from src.trends import calculate_trends


def _analyzed() -> pd.DataFrame:
    return pd.DataFrame({
        "review_id": ["1", "2", "3", "4"],
        "original_text": ["bad delivery", "great", "okay", "dark mode"],
        "clean_text": ["bad delivery", "great", "okay", "please add dark mode"],
        "rating": [1, 5, pd.NA, 4],
        "date": pd.date_range("2025-01-01", periods=4),
        "sentiment": ["Negative", "Positive", "Neutral", "Positive"],
        "sentiment_score": [-0.8, 0.8, 0.0, 0.5],
        "primary_theme": ["Delivery Experience", "Positive Feedback", "Other", "Feature Request"],
        "subtheme": ["Late delivery", "General praise", "Ambiguous", "Dark mode"],
        "classification_confidence": [0.9, 0.8, 0.2, 0.9],
        "is_feature_request": [False, False, False, True],
        "feature_request_group": [None, None, None, "Dark mode"],
        "feature_request_confidence": [0, 0, 0, 0.9],
    })


def test_metrics_are_consistent() -> None:
    dataframe = _analyzed()
    trends = calculate_trends(dataframe)
    themes = calculate_theme_summary(dataframe, trends)
    overall = calculate_overall_metrics(dataframe, themes, trends)
    assert round(
        overall.positive_feedback_percentage
        + overall.neutral_feedback_percentage
        + overall.negative_feedback_percentage,
        8,
    ) == 100
    assert overall.average_rating == (1 + 5 + 4) / 3
    assert overall.feature_request_count == 1
    assert themes["frequency"].sum() == 4
    assert round(themes["share_percentage"].sum(), 8) == 100
    assert themes["severity_score"].between(0, 100).all()


def test_feature_summary_counts_requests() -> None:
    summary = calculate_feature_request_summary(_analyzed())
    assert summary.iloc[0]["mentions"] == 1


def test_empty_data_does_not_crash() -> None:
    trends = calculate_trends(pd.DataFrame())
    assert calculate_overall_metrics(pd.DataFrame(), pd.DataFrame(), trends).total_feedback_items == 0
