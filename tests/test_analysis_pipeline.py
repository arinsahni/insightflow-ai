"""Integration tests for the local Phase 3 analysis pipeline."""

import pandas as pd

from src.analysis_pipeline import analyze_feedback
from src.data_cleaner import PRIMARY_COLUMNS


def _cleaned() -> pd.DataFrame:
    rows = [
        ("1", "Payment failed", "Payment failed", "2025-01-01", 1),
        ("2", "Great app", "Great app", "2025-01-20", 5),
        ("3", "Please add dark mode", "Please add dark mode", "2025-02-10", 4),
    ]
    dataframe = pd.DataFrame(rows, columns=["review_id", "original_text", "clean_text", "date", "rating"])
    for column in PRIMARY_COLUMNS[5:]:
        dataframe[column] = pd.NA
    dataframe["date"] = pd.to_datetime(dataframe["date"])
    dataframe["source_row_number"] = [2, 3, 4]
    return dataframe


def test_pipeline_produces_analysis_without_mutating_input_or_gemini() -> None:
    dataframe = _cleaned()
    original = dataframe.copy(deep=True)
    result = analyze_feedback(dataframe)
    required = {
        "sentiment", "sentiment_score", "negativity_score", "primary_theme",
        "secondary_theme", "subtheme", "classification_confidence",
        "classification_method", "is_feature_request", "feature_request_text",
        "feature_request_detected", "feature_request_confidence",
        "feature_request_group", "feature_request_method",
        "feature_request_matched_terms", "feature_request_score",
    }
    assert required.issubset(result.analyzed_reviews.columns)
    assert result.overall_metrics.total_feedback_items == 3
    assert not result.theme_summary.empty
    pd.testing.assert_frame_equal(dataframe, original)
